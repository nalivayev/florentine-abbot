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
            region=(0.35, 0.5, 0.5, 0.6),
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
            region=(0.25, 0.25, 0.5, 0.5),
            embedding=self._make_embedding(),
        )
        assert self.store.file_already_processed("/archive/img.jpg")

    def test_get_faces_by_file(self) -> None:
        img_file = self.store.get_or_create_file("/archive/group.jpg")
        for i in range(3):
            self.store.add_face(
                file=img_file,
                region=(0.25 + i * 0.1, 0.25, 0.5, 0.5),
                embedding=self._make_embedding(i),
            )
        other_file = self.store.get_or_create_file("/archive/other.jpg")
        self.store.add_face(
            file=other_file,
            region=(0.25, 0.25, 0.5, 0.5),
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
            region=(0.25, 0.25, 0.5, 0.5),
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
            file=img_a, region=(0.25, 0.25, 0.5, 0.5), embedding=self._make_embedding(1)
        )
        img_b = self.store.get_or_create_file("/b.jpg")
        face_b = self.store.add_face(
            file=img_b, region=(0.25, 0.25, 0.5, 0.5), embedding=self._make_embedding(2)
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
                file=img_file, region=(0.25, 0.25, 0.5, 0.5), embedding=self._make_embedding(i)
            )
        pairs = self.store.get_all_embeddings()
        assert len(pairs) == 5
        for fid, vec in pairs:
            assert isinstance(fid, int)
            assert vec.shape == (512,)

    def test_list_unconfirmed_clusters(self) -> None:
        file_a = self.store.get_or_create_file("/cluster-a.jpg")
        face_a1 = self.store.add_face(
            file=file_a,
            region=(0.25, 0.25, 0.5, 0.5),
            embedding=self._make_embedding(10),
        )
        face_a2 = self.store.add_face(
            file=file_a,
            region=(0.55, 0.25, 0.3, 0.3),
            embedding=self._make_embedding(11),
        )
        self.store.set_cluster(face_a1.id, 10)
        self.store.set_cluster(face_a2.id, 10)

        file_b = self.store.get_or_create_file("/cluster-b.jpg")
        face_b1 = self.store.add_face(
            file=file_b,
            region=(0.25, 0.25, 0.5, 0.5),
            embedding=self._make_embedding(20),
        )
        face_b2 = self.store.add_face(
            file=file_b,
            region=(0.55, 0.25, 0.3, 0.3),
            embedding=self._make_embedding(21),
        )
        self.store.set_cluster(face_b1.id, 11)
        self.store.set_cluster(face_b2.id, 11)
        person_b = self.store.create_person(name="Confirmed")
        self.store.assign_cluster_to_person(11, person_b.id)

        file_c = self.store.get_or_create_file("/cluster-c.jpg")
        face_c1 = self.store.add_face(
            file=file_c,
            region=(0.25, 0.25, 0.5, 0.5),
            embedding=self._make_embedding(30),
        )
        face_c2 = self.store.add_face(
            file=file_c,
            region=(0.55, 0.25, 0.3, 0.3),
            embedding=self._make_embedding(31),
        )
        self.store.set_cluster(face_c1.id, 12)
        self.store.set_cluster(face_c2.id, 12)
        person_c = self.store.create_person(name="Partial")
        self.store.assign_person(face_c1.id, person_c.id)

        clusters = {
            cluster.cluster_id: cluster
            for cluster in self.store.list_unconfirmed_clusters()
        }

        assert 10 in clusters
        assert clusters[10].face_count == 2
        assert clusters[10].assigned_face_count == 0
        assert clusters[10].distinct_person_count == 0

        assert 12 in clusters
        assert clusters[12].face_count == 2
        assert clusters[12].assigned_face_count == 1
        assert clusters[12].distinct_person_count == 1

        assert 11 not in clusters

    def test_get_faces_by_cluster(self) -> None:
        file_a = self.store.get_or_create_file("/group-a.jpg")
        face_a = self.store.add_face(
            file=file_a,
            region=(0.25, 0.25, 0.5, 0.5),
            embedding=self._make_embedding(40),
        )
        file_b = self.store.get_or_create_file("/group-b.jpg")
        face_b = self.store.add_face(
            file=file_b,
            region=(0.55, 0.25, 0.3, 0.3),
            embedding=self._make_embedding(41),
        )
        other_face = self.store.add_face(
            file=file_b,
            region=(0.75, 0.25, 0.2, 0.2),
            embedding=self._make_embedding(42),
        )
        self.store.set_cluster(face_a.id, 20)
        self.store.set_cluster(face_b.id, 20)
        self.store.set_cluster(other_face.id, 21)

        faces = self.store.get_faces_by_cluster(20)

        assert [face.id for face in faces] == [face_a.id, face_b.id]

    def test_assign_cluster_to_person(self) -> None:
        person = self.store.create_person(name="Alice")
        img_file = self.store.get_or_create_file("/assign-cluster.jpg")
        face_a = self.store.add_face(
            file=img_file,
            region=(0.25, 0.25, 0.5, 0.5),
            embedding=self._make_embedding(50),
        )
        face_b = self.store.add_face(
            file=img_file,
            region=(0.55, 0.25, 0.3, 0.3),
            embedding=self._make_embedding(51),
        )
        self.store.set_cluster(face_a.id, 30)
        self.store.set_cluster(face_b.id, 30)

        updated = self.store.assign_cluster_to_person(30, person.id)

        assert updated == 2
        assert self.store.get_face(face_a.id).person_id == person.id  # type: ignore[union-attr]
        assert self.store.get_face(face_b.id).person_id == person.id  # type: ignore[union-attr]

    def test_create_person_from_cluster(self) -> None:
        img_file = self.store.get_or_create_file("/create-person.jpg")
        face_a = self.store.add_face(
            file=img_file,
            region=(0.25, 0.25, 0.5, 0.5),
            embedding=self._make_embedding(60),
        )
        face_b = self.store.add_face(
            file=img_file,
            region=(0.55, 0.25, 0.3, 0.3),
            embedding=self._make_embedding(61),
        )
        self.store.set_cluster(face_a.id, 40)
        self.store.set_cluster(face_b.id, 40)

        person = self.store.create_person_from_cluster(40, name="New person", notes="Imported")

        assert person.name == "New person"
        assert person.notes == "Imported"
        assert self.store.get_face(face_a.id).person_id == person.id  # type: ignore[union-attr]
        assert self.store.get_face(face_b.id).person_id == person.id  # type: ignore[union-attr]

    def test_exclude_face_from_cluster(self) -> None:
        person = self.store.create_person(name="Cluster person")
        img_file = self.store.get_or_create_file("/exclude-face.jpg")
        face_a = self.store.add_face(
            file=img_file,
            region=(0.25, 0.25, 0.5, 0.5),
            embedding=self._make_embedding(70),
        )
        face_b = self.store.add_face(
            file=img_file,
            region=(0.55, 0.25, 0.3, 0.3),
            embedding=self._make_embedding(71),
        )
        self.store.set_cluster(face_a.id, 50)
        self.store.set_cluster(face_b.id, 50)
        self.store.assign_cluster_to_person(50, person.id)

        self.store.exclude_face_from_cluster(face_a.id)

        excluded = self.store.get_face(face_a.id)
        kept = self.store.get_face(face_b.id)
        assert excluded is not None
        assert kept is not None
        assert excluded.cluster is None
        assert excluded.person_id is None
        assert kept.cluster == 50
        assert kept.person_id == person.id

