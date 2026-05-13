package com.arek.vintedpricer.vintedpricerapi.dto;

import java.util.List;

public class ClothingAnalysisResponse {
    public String itemType;
    public String brand;
    public String color;
    public String style;
    public String condition;
    public String conditionScore;

    public Integer lowPrice;
    public Integer mediumPrice;
    public Integer highPrice;
    public String priceComment;

    public String suggestedTitle;
    public String suggestedDescription;
    public List<String> keywords;

    public List<String> searchQueries;
    public List<SimilarOffer> similarOffers;

    public Double averagePrice;
    public Double medianPrice;
    public Integer minPrice;
    public Integer maxPrice;
    public Integer offersAnalyzed;

    public Integer opportunityScore;
    public String uploadedImageUrl;
}