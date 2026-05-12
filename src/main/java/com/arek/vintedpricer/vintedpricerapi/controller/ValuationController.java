package com.arek.vintedpricer.vintedpricerapi.controller;

import com.arek.vintedpricer.vintedpricerapi.dto.ClothingAnalysisResponse;
import com.arek.vintedpricer.vintedpricerapi.service.OpenAiVisionService;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@CrossOrigin(origins = "http://localhost:5173")
@RestController
public class ValuationController {

    private final OpenAiVisionService openAiVisionService;

    public ValuationController(
            OpenAiVisionService openAiVisionService
    ) {
        this.openAiVisionService = openAiVisionService;
    }

    @GetMapping("/api/test")
    public String test() {
        return "API działa";
    }

    @PostMapping("/api/analyze")
    public ClothingAnalysisResponse analyzeImage(
            @RequestParam("images")
            MultipartFile[] images
    ) {
        return openAiVisionService
                .analyzeClothing(images);
    }
}