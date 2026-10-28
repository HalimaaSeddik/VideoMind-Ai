from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from app.video_service import process_video
from app.rag.qa import answer_question

from .serializers import (
    AskQuestionSerializer,
    ProcessVideoSerializer,
)


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
