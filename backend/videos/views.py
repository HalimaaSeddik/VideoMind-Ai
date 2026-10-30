from django.shortcuts import render
import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from app.video_service import process_video
from app.rag.qa import answer_question

from .serializers import (
    AskQuestionSerializer,
    ProcessVideoSerializer,
    VideoSummarySerializer,
)

import json
from pathlib import Path

from django.conf import settings


from app.pipline import summarize_video
logger = logging.getLogger(__name__)




@api_view(["GET"])
def health_check(request):
    """Check whether the API is running."""

    return Response(
        {
            "status": "ok",
            "service": "VideoMind AI API",
        }
    )


@api_view(["POST"])
def process_video_view(request):
    """Process and index a YouTube video."""

    serializer = ProcessVideoSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        metadata = process_video(
            video_url=serializer.validated_data["url"],
        )

        return Response(
            {
                "message": "Video is ready.",
                "video": metadata,
            },
            status=status.HTTP_200_OK,
        )

    except ValueError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception:
        logger.exception("Video processing failed")

        return Response(
            {
                "error": (
                    "Video processing failed. "
                    "Check the backend logs for details."
                )
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def ask_question_view(request, video_id):
    """Answer a question using an indexed video's transcript."""

    serializer = AskQuestionSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = answer_question(
            video_id=video_id,
            question=serializer.validated_data["question"],
            language=serializer.validated_data["language"],
        )

        return Response(result, status=status.HTTP_200_OK)

    except ValueError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception:
        return Response(
            {
                "error": (
                    "Could not answer the question. "
                    "Check the backend logs for details."
                )
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )



@api_view(["POST"])
def video_summary_view(request, video_id):
    serializer = VideoSummarySerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    language = serializer.validated_data["language"]

    project_root = Path(settings.BASE_DIR).parent
    metadata_path = (
        project_root / "data" / "videos" / f"{video_id}.json"
    )

    if not metadata_path.exists():
        return Response(
            {"error": "Video not found. Process the video first."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        import json

        with metadata_path.open("r", encoding="utf-8") as file:
            metadata = json.load(file)

        result = summarize_video(
            video_url=metadata["source_url"],
            language=language,
        )

        return Response(
            {
                "video_id": video_id,
                "summary": result["final_summary"],
                "partial_summaries": result["partial_summaries"],
            },
            status=status.HTTP_200_OK,
        )

    except ValueError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception:
        logger.exception(
            "Summary generation failed for video %s",
            video_id,
        )

        return Response(
            {
                "error": (
                    "Summary generation failed. "
                    "Check the Django terminal for details."
                )
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
