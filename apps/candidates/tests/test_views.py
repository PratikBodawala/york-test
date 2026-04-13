from django.test import SimpleTestCase

from apps.candidates.views import derive_candidate_identity


class CandidateUploadTests(SimpleTestCase):
    def test_derive_candidate_identity_from_filename(self):
        candidate_data = derive_candidate_identity("alice_martin_resume.pdf")

        self.assertEqual(candidate_data["first_name"], "Alice")
        self.assertEqual(candidate_data["last_name"], "Martin")
        self.assertEqual(candidate_data["headline"], "Alice Martin")
        self.assertTrue(candidate_data["email"].endswith("@local.resume"))
