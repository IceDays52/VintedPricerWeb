package com.arek.vintedpricer.vintedpricerapi.service;

import com.arek.vintedpricer.vintedpricerapi.dto.ClothingAnalysisResponse;
import com.arek.vintedpricer.vintedpricerapi.dto.SimilarOffer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.reactive.function.client.WebClient;

import java.net.URI;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class SimilarOffersSearchService {

    @Value("${google.search.api.key:}")
    private String apiKey;

    @Value("${google.search.cx:}")
    private String cx;

    private final WebClient webClient =
            WebClient.builder()
                    .baseUrl("https://www.googleapis.com")
                    .build();

    public List<String> buildSearchQueries(ClothingAnalysisResponse analysis) {
        String brand = cleanTerm(analysis.brand);
        String itemType = cleanTerm(analysis.itemType);
        String color = cleanTerm(analysis.color);

        List<String> baseTerms = new ArrayList<>();

        if (StringUtils.hasText(brand)) {
            baseTerms.add(brand);
        }

        if (StringUtils.hasText(itemType)) {
            baseTerms.add(itemType);
        }

        String baseQuery = String.join(" ", baseTerms).trim();

        if (!StringUtils.hasText(baseQuery)) {
            baseQuery = "ubranie";
        }

        List<String> queries = new ArrayList<>();

        queries.add(baseQuery + " Vinted");
        queries.add(baseQuery + " OLX");
        queries.add(baseQuery + " Allegro");

        if (StringUtils.hasText(color)) {
            queries.add(baseQuery + " " + color + " używane");
        }

        return queries;
    }

    public List<SimilarOffer> findSimilarOffers(
            ClothingAnalysisResponse analysis
    ) {
        if (!StringUtils.hasText(apiKey)
                || !StringUtils.hasText(cx)) {
            return List.of();
        }

        List<String> queries = buildSearchQueries(analysis);
        Map<String, SimilarOffer> uniqueOffers =
                new LinkedHashMap<>();

        for (String query : queries) {
            try {
                Map response = webClient.get()
                        .uri(builder -> builder
                                .path("/customsearch/v1")
                                .queryParam("key", apiKey)
                                .queryParam("cx", cx)
                                .queryParam("q", query)
                                .queryParam("num", 5)
                                .build())
                        .retrieve()
                        .bodyToMono(Map.class)
                        .block();

                if (response == null) {
                    continue;
                }

                List items =
                        (List) response.getOrDefault(
                                "items",
                                List.of()
                        );

                for (Object itemObject : items) {
                    Map item =
                            (Map) itemObject;

                    SimilarOffer offer =
                            mapGoogleItemToOffer(item);

                    if (!StringUtils.hasText(offer.link)) {
                        continue;
                    }

                    uniqueOffers.putIfAbsent(
                            offer.link,
                            offer
                    );

                    if (uniqueOffers.size() >= 8) {
                        return new ArrayList<>(
                                uniqueOffers.values()
                        );
                    }
                }

            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        return new ArrayList<>(
                uniqueOffers.values()
        );
    }

    private SimilarOffer mapGoogleItemToOffer(Map item) {
        SimilarOffer offer = new SimilarOffer();

        offer.title =
                Objects.toString(item.get("title"), "");

        offer.link =
                Objects.toString(item.get("link"), "");

        offer.snippet =
                Objects.toString(item.get("snippet"), "");

        offer.source =
                extractSource(offer.link);

        offer.imageUrl =
                extractImageUrl(item);

        offer.detectedPrice =
                extractPrice(
                        offer.title + " " + offer.snippet
                );

        return offer;
    }

    private String cleanTerm(String value) {
        if (!StringUtils.hasText(value)) {
            return "";
        }

        if (value.equalsIgnoreCase("Nieznana")
                || value.equalsIgnoreCase("Nieznany")
                || value.equalsIgnoreCase("Błąd analizy")) {
            return "";
        }

        return value.trim();
    }

    private String extractSource(String link) {
        try {
            String host =
                    URI.create(link).getHost();

            if (host == null) {
                return "";
            }

            return host.replace("www.", "");

        } catch (Exception e) {
            return "";
        }
    }

    private String extractImageUrl(Map item) {
        try {
            Map pagemap =
                    (Map) item.get("pagemap");

            if (pagemap == null) {
                return "";
            }

            List thumbnails =
                    (List) pagemap.get("cse_thumbnail");

            if (thumbnails == null
                    || thumbnails.isEmpty()) {
                return "";
            }

            Map firstThumbnail =
                    (Map) thumbnails.get(0);

            return Objects.toString(
                    firstThumbnail.get("src"),
                    ""
            );

        } catch (Exception e) {
            return "";
        }
    }

    private Integer extractPrice(String text) {
        Matcher matcher = Pattern
                .compile(
                        "(\\d{2,5})\\s*(zł|zl|pln)",
                        Pattern.CASE_INSENSITIVE
                )
                .matcher(text);

        if (!matcher.find()) {
            return null;
        }

        try {
            return Integer.parseInt(
                    matcher.group(1)
            );

        } catch (Exception e) {
            return null;
        }
    }
}
