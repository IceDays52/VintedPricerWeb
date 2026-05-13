package com.arek.vintedpricer.vintedpricerapi.service;

import com.arek.vintedpricer.vintedpricerapi.dto.ClothingAnalysisResponse;
import com.arek.vintedpricer.vintedpricerapi.dto.SimilarOffer;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
public class PythonPricingService {

    private static final Logger log =
            LoggerFactory.getLogger(PythonPricingService.class);

    @Value("${python.ai.base-url}")
    private String pythonAiBaseUrl;

    private final WebClient webClient =
            WebClient.builder().build();

    public void enrichWithPythonPricing(
            ClothingAnalysisResponse result
    ) {

        String query = buildVintedQuery(result);

        try {

            Map response = webClient.get()
                    .uri(
                            pythonAiBaseUrl
                                    + "/vinted-offers?query={query}",
                            query
                    )
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();

            if (
                    response != null
                            && !response.containsKey("error")
            ) {

                result.averagePrice =
                        toDouble(response.get("average_price_pln"));

                result.medianPrice =
                        toDouble(response.get("median_price_pln"));

                result.minPrice =
                        toInteger(response.get("min_price_pln"));

                result.maxPrice =
                        toInteger(response.get("max_price_pln"));

                result.offersAnalyzed =
                        toInteger(response.get("offers_analyzed"));

                result.priceComment =
                        (String) response.get("comment");

                if (
                        response.get("similarOffers")
                                instanceof List<?> rawList
                ) {

                    List<SimilarOffer> mappedOffers =
                            new ArrayList<>();

                    for (Object obj : rawList) {

                        Map<String, Object> map =
                                (Map<String, Object>) obj;

                        SimilarOffer offer =
                                new SimilarOffer();

                        offer.title =
                                (String) map.get("title");

                        offer.link =
                                (String) map.get("link");

                        offer.source =
                                (String) map.get("source");

                        offer.detectedPrice =
                                toInteger(
                                        map.get("detectedPrice")
                                );

                        offer.snippet =
                                (String) map.get("snippet");

                        offer.brand =
                                (String) map.get("brand");

                        offer.size =
                                (String) map.get("size");

                        offer.dealScore =
                                toInteger(
                                        map.get("dealScore")
                                );

                        offer.dealLabel =
                                (String) map.get("dealLabel");

                        mappedOffers.add(offer);
                    }

                    result.similarOffers = mappedOffers;
                }
            }

        } catch (Exception e) {

            log.error(
                    "Python pricing service error",
                    e
            );

            result.priceComment =
                    "AI podało wycenę, ale nie udało się "
                            + "pobrać podobnych ofert z Vinted.";
        }
    }

    private String buildVintedQuery(
            ClothingAnalysisResponse result
    ) {

        String brand =
                cleanText(result.brand);

        String itemType =
                cleanText(result.itemType);

        String title =
                cleanText(result.suggestedTitle);

        String query;

        if (
                brand != null
                        && itemType != null
        ) {

            query = brand + " " + itemType;

        } else if (
                brand != null
                        && title != null
        ) {

            query = brand + " " + title;

        } else if (title != null) {

            query = title;

        } else if (
                result.searchQueries != null
                        && !result.searchQueries.isEmpty()
        ) {

            query = result.searchQueries.get(0);

        } else {

            query = "";
        }

        return query
                .replaceAll("(?i)\\bvinted\\b", "")
                .replaceAll("(?i)\\bolx\\b", "")
                .replaceAll("(?i)\\ballegro\\b", "")
                .replaceAll("\\s+", " ")
                .trim();
    }

    private String cleanText(String value) {

        if (
                value == null
                        || value.isBlank()
        ) {
            return null;
        }

        return value
                .replaceAll("(?i)\\bvinted\\b", "")
                .replaceAll("(?i)\\bolx\\b", "")
                .replaceAll("(?i)\\ballegro\\b", "")
                .replaceAll(",", " ")
                .replaceAll("\\s+", " ")
                .trim();
    }

    private Integer toInteger(Object v) {

        return (v instanceof Number n)
                ? n.intValue()
                : null;
    }

    private Double toDouble(Object v) {

        return (v instanceof Number n)
                ? n.doubleValue()
                : null;
    }
}