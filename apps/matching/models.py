from django.db import models


class MatchStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class JobRequest(models.Model):
    title = models.CharField(max_length=255)
    description_text = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=MatchStatus.choices,
        default=MatchStatus.PENDING,
    )
    retrieval_k = models.PositiveIntegerField(default=50)
    top_k = models.PositiveIntegerField(default=10)
    error_message = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class CandidateMatch(models.Model):
    job_request = models.ForeignKey(
        JobRequest,
        on_delete=models.CASCADE,
        related_name="matches",
    )
    candidate = models.ForeignKey(
        "candidates.Candidate",
        on_delete=models.CASCADE,
        related_name="matches",
    )
    rank = models.PositiveIntegerField()
    retrieval_score = models.FloatField(default=0.0)
    fit_score = models.FloatField(default=0.0)
    final_score = models.FloatField(default=0.0)
    matched_skills = models.JSONField(default=list, blank=True)
    risks = models.JSONField(default=list, blank=True)
    explanation = models.TextField(blank=True)
    supporting_chunks = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rank", "-final_score"]
        unique_together = ("job_request", "candidate")

    def __str__(self) -> str:
        return f"{self.job_request_id}:{self.rank}:{self.candidate.display_name}"
