"""
Unit tests for face_recognizer.store (no DeepFace dependency required).
"""

from contextlib import ExitStack
import io
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy
from face_recognizer.store import RecognizerStore


class TestRecognizerStore:
    """Regression coverage for RecognizerStore without pytest fixtures."""

    def setup_method(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.archive_path = Path(self.temp_dir.name)
        self._stack = ExitStack()
        self.store = self._stack.enter_context(RecognizerStore(self.archive_path))

    def teardown_method(self) -> None:
        self._stack.close()
        self.temp_dir.cleanup()

    @staticmethod
    def _embedding_to_bytes(vec: numpy.ndarray) -> bytes:
        buf = io.BytesIO()
        numpy.save(buf, vec.astype(numpy.float32))
        return buf.getvalue()

    @staticmethod
    def _bytes_to_embedding(data: bytes) -> numpy.ndarray:
        return numpy.load(io.BytesIO(data))

    @staticmethod
    def _make_embedding(seed: int = 0) -> numpy.ndarray:
        rng = numpy.random.default_rng(seed)
        vec = rng.random(512).astype(numpy.float32)
        return vec / numpy.linalg.norm(vec)

    def test_embedding_round_trip(self) -> None:
        original = numpy.random.randn(512).astype(numpy.float32)
        recovered = self._bytes_to_embedding(self._embedding_to_bytes(original))
        numpy.testing.assert_array_almost_equal(original, recovered)

    def test_add_and_retrieve_face(self) -> None:
        vec = self._make_embedding()
        img_file = self.store.get_or_create_file("/archive/2020/img.PRV.jpg")
        face = self.store.add_face(
            file=img_file,
            bbox=(20, 40, 100, 120),
            image_size=(200, 200),
            embedding=vec,
            confidence=0.97,
        )
        assert face.id is not None
        assert face.confidence is not None
        assert abs(face.confidence - 0.97) < 1e-9
        assert abs(face.center_x - 0.35) < 1e-9
        assert abs(face.center_y - 0.5) < 1e-9
        assert abs(face.width - 0.5) < 1e-9
        assert abs(face.height - 0.6) < 1e-9

        fetched = self.store.get_face(face.id)
        assert fetched is not None
        assert Path(fetched.file.file_path) == Path("/archive/2020/img.PRV.jpg")
        assert abs(fetched.center_x - 0.35) < 1e-9
        assert abs(fetched.center_y - 0.5) < 1e-9
        assert abs(fetched.width - 0.5) < 1e-9
        assert abs(fetched.height - 0.6) < 1e-9
        numpy.testing.assert_array_almost_equal(
            self._bytes_to_embedding(fetched.embedding), vec
        )

    def test_file_already_processed(self) -> None:
        assert not self.store.file_already_processed("/archive/img.jpg")

        img_file = self.store.get_or_create_file("/archive/img.jpg")
        self.store.add_face(
            file=img_file,
            bbox=(0, 0, 50, 50),
            image_size=(100, 100),
            embedding=self._make_embedding(),
        )
        assert self.store.file_already_processed("/archive/img.jpg")

    def test_get_faces_by_file(self) -> None:
        img_file = self.store.get_or_create_file("/archive/group.jpg")
        for i in range(3):
            self.store.add_face(
                file=img_file,
                bbox=(i * 10, 0, 50, 50),
                image_size=(100, 100),
                embedding=self._make_embedding(i),
            )
        other_file = self.store.get_or_create_file("/archive/other.jpg")
        self.store.add_face(
            file=other_file,
            bbox=(0, 0, 50, 50),
            image_size=(100, 100),
            embedding=self._make_embedding(99),
        )

        faces = self.store.get_faces_by_file("/archive/group.jpg")
        assert len(faces) == 3

    def test_person_lifecycle(self) -> None:
        person = self.store.create_person(name="Alice", notes="Test person")
        assert person.id is not None
        assert person.name == "Alice"

        same = self.store.get_or_create_person("Alice")
        assert same.id == person.id

        new_person = self.store.get_or_create_person("Bob")
        assert new_person.id != person.id
        assert new_person.name == "Bob"

    def test_assign_person(self) -> None:
        person = self.store.create_person()
        img_file = self.store.get_or_create_file("/img.jpg")
        face = self.store.add_face(
            file=img_file,
            bbox=(0, 0, 50, 50),
            image_size=(100, 100),
            embedding=self._make_embedding(),
        )
        assert face.person_id is None

        self.store.assign_person(face.id, person.id)
        fetched = self.store.get_face(face.id)
        assert fetched is not None
        assert fetched.person_id == person.id

    def test_get_faces_without_cluster(self) -> None:
        img_a = self.store.get_or_create_file("/a.jpg")
        face_a = self.store.add_face(
            file=img_a, bbox=(0, 0, 50, 50), image_size=(100, 100), embedding=self._make_embedding(1)
        )
        img_b = self.store.get_or_create_file("/b.jpg")
        face_b = self.store.add_face(
            file=img_b, bbox=(0, 0, 50, 50), image_size=(100, 100), embedding=self._make_embedding(2)
        )
        self.store.set_cluster(face_a.id, 0)

        unclustered = self.store.get_faces_without_cluster()
        ids = [f.id for f in unclustered]
        assert face_b.id in ids
        assert face_a.id not in ids

    def test_get_all_embeddings(self) -> None:
        for i in range(5):
            img_file = self.store.get_or_create_file(f"/img{i}.jpg")
            self.store.add_face(
                file=img_file, bbox=(0, 0, 50, 50), image_size=(100, 100), embedding=self._make_embedding(i)
            )
        pairs = self.store.get_all_embeddings()
        assert len(pairs) == 5
        for fid, vec in pairs:
            assert isinstance(fid, int)
            assert vec.shape == (512,)

