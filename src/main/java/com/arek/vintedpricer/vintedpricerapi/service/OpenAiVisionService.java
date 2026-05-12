package com.arek.vintedpricer.vintedpricerapi.service;

import com.arek.vintedpricer.vintedpricerapi.dto.ClothingAnalysisResponse;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Map;

@Service
public class OpenAiVisionService {

    @Value("${gemini.api.key}")
    private String apiKey;

    private final SimilarOffersSearchService similarOffersSearchService;
    private final PythonPricingService pythonPricingService;

    private final WebClient webClient =
            WebClient.builder().build();

    private final ObjectMapper objectMapper =
            new ObjectMapper();

    public OpenAiVisionService(
            SimilarOffersSearchService similarOffersSearchService,
            PythonPricingService pythonPricingService
    ) {
        this.similarOffersSearchService = similarOffersSearchService;
        this.pythonPricingService = pythonPricingService;
    }

    public ClothingAnalysisResponse analyzeClothing(
            MultipartFile[] images
    ) {
        try {
            List<Object> parts = new ArrayList<>();

            parts.add(
                    Map.of(
                            "text",
                            """
                            Przeanalizuj ubranie ze zdjęć.
            
                            Odpowiedz wyłącznie poprawnym JSON-em.
                            Nie dodawaj markdown, komentarzy ani tekstu poza JSON-em.
            
                            Jeśli nie rozpoznasz marki, wpisz "Nieznana".
                            Ceny lowPrice, mediumPrice i highPrice podaj w PLN dla rynku odzieży używanej w Polsce.
                            Nie ustawiaj cen na 0, jeśli da się rozsądnie oszacować wartość.
            
                            Bardzo ważne:
                            Spróbuj rozpoznać dokładny model, serię, kolaborację, limitowaną edycję albo projektanta.
                            Jeśli widzisz charakterystyczne elementy, uwzględnij je w nazwie i słowach kluczowych.
            
                            Dla butów zwracaj uwagę na:
                            - dokładny model
                            - edycję specjalną
                            - kolaborację
                            - projektanta
                            - motyw graficzny
                            - postać lub serię, np. Disney, Mickey Mouse
            
                            Dla Adidas zwracaj szczególną uwagę na:
                            - Forum Hi
                            - Forum Mid
                            - Jeremy Scott
                            - Adidas x Disney
                            - Mickey Mouse
                            - Wings
                            - JS
            
                            Pole suggestedTitle ma być możliwie najbardziej wyszukiwalne.
                            Przykład:
                            "Adidas Jeremy Scott Forum Hi Mickey Mouse Disney sneakersy"
            
                            Pole searchQueries ma zawierać 3-5 fraz do wyszukiwania podobnych ofert.
                            Frazy mają być krótkie, konkretne i nadawać się do wyszukiwania na Vinted/Google.
            
                            Zwróć dokładnie taki JSON:
                            {
                              "itemType": "",
                              "brand": "",
                              "color": "",
                              "style": "",
                              "condition": "",
                              "conditionScore": "",
                              "lowPrice": 0,
                              "mediumPrice": 0,
                              "highPrice": 0,
                              "priceComment": "",
                              "suggestedTitle": "",
                              "suggestedDescription": "",
                              "keywords": [],
                              "searchQueries": []
                            }
                            """
                    )
            );

            for (MultipartFile image : images) {
                String base64Image =
                        Base64.getEncoder()
                                .encodeToString(image.getBytes());

                parts.add(
                        Map.of(
                                "inline_data",
                                Map.of(
                                        "mime_type",
                                        image.getContentType() != null
                                                ? image.getContentType()
                                                : "image/jpeg",
                                        "data",
                                        base64Image
                                )
                        )
                );
            }

            Map<String, Object> requestBody = Map.of(
                    "contents",
                    List.of(
                            Map.of(
                                    "parts",
                                    parts
                            )
                    ),
                    "generationConfig",
                    Map.of(
                            "temperature", 0.3,
                            "responseMimeType", "application/json"
                    )
            );

            Map response = webClient.post()
                    .uri(
                            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key="
                                    + apiKey
                    )
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();

            String jsonText = extractJsonText(response);

            ClothingAnalysisResponse result =
                    objectMapper.readValue(
                            jsonText,
                            ClothingAnalysisResponse.class
                    );

            result.searchQueries =
                    similarOffersSearchService.buildSearchQueries(result);

            result.similarOffers =
                    similarOffersSearchService.findSimilarOffers(result);

            pythonPricingService.enrichWithPythonPricing(result);

            return result;

        } catch (WebClientResponseException e) {
            e.printStackTrace();

            return createErrorResponse(
                    "Gemini API error "
                            + e.getStatusCode()
                            + ": "
                            + e.getResponseBodyAsString()
            );

        } catch (Exception e) {
            e.printStackTrace();

            return createErrorResponse(
                    "Błąd aplikacji: " + e.getMessage()
            );
        }
    }

    private String extractJsonText(Map response) {
        if (response == null) {
            throw new IllegalStateException("Gemini response is null.");
        }

        List candidates =
                (List) response.get("candidates");

        if (candidates == null || candidates.isEmpty()) {
            throw new IllegalStateException(
                    "Gemini response does not contain candidates."
            );
        }

        Map candidate =
                (Map) candidates.get(0);

        Map content =
                (Map) candidate.get("content");

        List responseParts =
                (List) content.get("parts");

        Map firstPart =
                (Map) responseParts.get(0);

        return firstPart.get("text")
                .toString()
                .replace("```json", "")
                .replace("```", "")
                .trim();
    }

    private ClothingAnalysisResponse createErrorResponse(String message) {
        ClothingAnalysisResponse error =
                new ClothingAnalysisResponse();

        error.itemType = "Błąd analizy";
        error.brand = "Nieznana";
        error.color = "Nieznany";
        error.style = "Nieznany";
        error.condition = "Nieznany";
        error.conditionScore = "0/10";

        error.lowPrice = 0;
        error.mediumPrice = 0;
        error.highPrice = 0;

        error.averagePrice = null;
        error.medianPrice = null;
        error.opportunityScore = null;

        error.priceComment = message;

        error.suggestedTitle =
                "Nie udało się przeanalizować";

        error.suggestedDescription =
                "Spróbuj ponownie za chwilę.";

        error.keywords = List.of();
        error.searchQueries = List.of();
        error.similarOffers = List.of();

        return error;
    }
}
