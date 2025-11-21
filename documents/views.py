from rest_framework import viewsets
from rest_framework.decorators import action
from .utils import extract_pdf_text
from .models import Document
from .serializers import DocumentSerializer
# Create your views here.


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def perform_create(self, serializer):
        # Extrahiere den Text aus der PDF, wenn ein neues Dokument erstellt wird
        file = serializer.validated_data.get('file')
        # Extrahiere den Text der PDF-Datei
        extracted_text = extract_pdf_text(file.path)

        # Speichere das Dokument mit dem extrahierten Text
        serializer.save(extracted_text=extracted_text)

    @action(detail=True, methods=['get'])
    def get_extracted_text(self, request, pk=None):
        # Holen des Dokuments anhand der ID (primary key)
        document = self.get_object()
        # Gebe den extrahierten Text des Dokuments zurück
        return Response({'extracted_text': document.extracted_text})
