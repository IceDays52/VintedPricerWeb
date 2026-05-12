package com.arek.vintedpricer.vintedpricerapi.service;

import com.arek.vintedpricer.vintedpricerapi.dto.ClothingAnalysisResponse;
import com.arek.vintedpricer.vintedpricerapi.dto.SimilarOffer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
public class PythonPricingService {

    @Value("${python.ai.base-url}")
    private String pythonAiBaseUrl;

    private final WebClient webClient = WebClient.builder().build();

    public void enrichWithPythonPricing(ClothingAnalysisResponse result) {
        String query;

        if (result.searchQueries != null && !result.searchQueries.isEmpty()) {
            query = result.searchQueries.get(0);
        } else {
            query = result.suggestedTitle;
        }

        try {
            Map response = webClient.get()
                    .uri(pythonAiBaseUrl + "/vinted-offers?query={query}", query)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();

            if (response != null && !response.containsKey("error")) {

                // TYLKO średnia i mediana z Pythona
                result.averagePrice = toDouble(response.get("average_price_pln"));
                result.medianPrice = toDouble(response.get("median_price_pln"));

                // lowPrice / mediumPrice / highPrice zostają z AI
                result.priceComment = (String) response.get("comment");

                if (response.get("similarOffers") instanceof List<?> rawList) {
                    List<SimilarOffer> mappedOffers = new ArrayList<>();

                    for (Object obj : rawList) {
                        Map<String, Object> map = (Map<String, Object>) obj;

                        SimilarOffer offer = new SimilarOffer();
                        offer.title = (String) map.get("title");
                        offer.link = (String) map.get("link");
                        offer.source = (String) map.get("source");
                        offer.detectedPrice = toInteger(map.get("detectedPrice"));
                        offer.snippet = (String) map.get("snippet");

                        mappedOffers.add(offer);
                    }

                    result.similarOffers = mappedOffers;
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
            result.priceComment = "AI podało wycenę, ale nie udało się pobrać podobnych ofert z Vinted.";
        }
    }

    private Integer toInteger(Object v) {
        return (v instanceof Number n) ? n.intValue() : null;
    }

    private Double toDouble(Object v) {
        return (v instanceof Number n) ? n.doubleValue() : null;
    }
}