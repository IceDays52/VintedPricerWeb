import { useState } from "react";
import axios from "axios";
import "./App.css";

type SimilarOffer = {
    title: string;
    link: string;
    source: string;
    snippet: string;
    imageUrl?: string;
    detectedPrice?: number;
    opportunityScore?: number;
    badge?: string;
};

type AnalysisResult = {
    itemType: string;
    brand: string;
    color: string;
    style: string;
    condition: string;
    conditionScore: string;

    lowPrice: number;
    mediumPrice: number;
    highPrice: number;

    averagePrice?: number;
    medianPrice?: number;
    opportunityScore?: number;

    priceComment: string;

    suggestedTitle: string;
    suggestedDescription: string;

    keywords: string[];
    searchQueries: string[];
    similarOffers: SimilarOffer[];
};

function App() {
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [previewUrls, setPreviewUrls] = useState<string[]>([]);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [loading, setLoading] = useState(false);

    const handleFileChange = (
        event: React.ChangeEvent<HTMLInputElement>
    ) => {
        const files = Array.from(
            event.target.files || []
        ).slice(0, 3);

        setSelectedFiles(files);

        setPreviewUrls(
            files.map((file) =>
                URL.createObjectURL(file)
            )
        );

        setResult(null);
    };

    const analyzeImage = async () => {
        if (selectedFiles.length === 0) {
            alert("Dodaj minimum 1 zdjęcie");
            return;
        }

        try {
            setLoading(true);

            const formData = new FormData();

            selectedFiles.forEach((file) => {
                formData.append("images", file);
            });

            const response = await axios.post(
                "http://localhost:8080/api/analyze",
                formData,
                {
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                }
            );

            console.log("WYNIK Z BACKENDU:", response.data);

            setResult(response.data);

        } catch (error) {
            console.error(error);
            alert("Błąd analizy zdjęcia");

        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="app">

            <section className="heroSection">
                <div>
                    <span className="pill">
                        AI clothing valuation
                    </span>

                    <h1>Vinted Pricer</h1>

                    <p>
                        Wrzuć do 3 zdjęć ubrania i wygeneruj
                        wycenę, opis oraz tytuł ogłoszenia.
                    </p>
                </div>
            </section>

            <section className="layout">

                <aside className="leftPanel">

                    <div className="uploadCard">
                        <h2>Zdjęcia produktu</h2>

                        <p>
                            Dodaj maksymalnie 3 zdjęcia.
                        </p>

                        <label className="uploadButton">
                            <input
                                type="file"
                                accept="image/jpeg,image/png,image/webp"
                                multiple
                                onChange={handleFileChange}
                            />

                            Wybierz zdjęcia
                        </label>
                    </div>

                    <div className="imagesGrid">

                        {previewUrls.length > 0 ? (
                            previewUrls.map((url, index) => (
                                <div
                                    className="imageCard"
                                    key={index}
                                >
                                    <img
                                        src={url}
                                        alt={`preview-${index}`}
                                        className="previewImage"
                                    />
                                </div>
                            ))
                        ) : (
                            <div className="emptyPreview">
                                Brak zdjęć
                            </div>
                        )}

                    </div>

                    <button
                        className="analyzeButton"
                        onClick={analyzeImage}
                        disabled={loading}
                    >
                        {loading
                            ? "Analizuję..."
                            : "Analizuj ubranie"}
                    </button>

                </aside>

                <section className="rightPanel">

                    {!result && !loading && (
                        <div className="placeholderCard">
                            <h2>
                                Wynik analizy pojawi się tutaj
                            </h2>

                            <p>
                                AI oceni markę, stan, styl,
                                wycenę i wygeneruje opis.
                            </p>
                        </div>
                    )}

                    {loading && (
                        <div className="placeholderCard">
                            <div className="spinner"></div>

                            <h2>
                                AI analizuje ubranie...
                            </h2>
                        </div>
                    )}

                    {result && (
                        <>

                            <div className="resultHeader">
                                <span className="pill dark">
                                    Analiza AI
                                </span>

                                <h2>
                                    {result.suggestedTitle}
                                </h2>
                            </div>

                            <div className="priceGrid">

                                <div className="priceBox">
                                    <span>
                                        Szybka sprzedaż
                                    </span>

                                    <strong>
                                        {result.lowPrice} zł
                                    </strong>
                                </div>

                                <div className="priceBox featured">
                                    <span>
                                        Cena rekomendowana
                                    </span>

                                    <strong>
                                        {result.mediumPrice} zł
                                    </strong>
                                </div>

                                <div className="priceBox">
                                    <span>
                                        Wysoka cena
                                    </span>

                                    <strong>
                                        {result.highPrice} zł
                                    </strong>
                                </div>

                            </div>

                            <div className="infoGrid">

                                <InfoCard
                                    title="Typ ubrania"
                                    value={result.itemType}
                                />

                                <InfoCard
                                    title="Marka"
                                    value={result.brand}
                                />

                                <InfoCard
                                    title="Kolor"
                                    value={result.color}
                                />

                                <InfoCard
                                    title="Styl"
                                    value={result.style}
                                />

                                <InfoCard
                                    title="Stan"
                                    value={`${result.condition} (${result.conditionScore})`}
                                />

                                <InfoCard
                                    title="Średnia cena"
                                    value={
                                        result.averagePrice !== undefined &&
                                        result.averagePrice !== null
                                            ? `${result.averagePrice} zł`
                                            : "Brak danych"
                                    }
                                />

                                <InfoCard
                                    title="Mediana ceny"
                                    value={
                                        result.medianPrice !== undefined &&
                                        result.medianPrice !== null
                                            ? `${result.medianPrice} zł`
                                            : "Brak danych"
                                    }
                                />

                                <InfoCard
                                    title="Okazja"
                                    value={
                                        result.opportunityScore !== undefined &&
                                        result.opportunityScore !== null
                                            ? `${result.opportunityScore}/100`
                                            : "Brak danych"
                                    }
                                />

                                <InfoCard
                                    title="Komentarz AI"
                                    value={result.priceComment}
                                />

                            </div>

                            <div className="bigCard">

                                <h3>
                                    Opis ogłoszenia
                                </h3>

                                <p>
                                    {result.suggestedDescription}
                                </p>

                            </div>

                            <div className="bigCard">

                                <h3>
                                    Podobne oferty
                                </h3>


                                {result.similarOffers?.length > 0 ? (

                                    <div className="offersGrid">

                                        {result.similarOffers.map(
                                            (offer, index) => (

                                                <a
                                                    className="offerCard"
                                                    href={offer.link}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    key={index}
                                                >

                                                    {offer.imageUrl ? (
                                                        <img
                                                            src={offer.imageUrl}
                                                            alt={offer.title}
                                                        />
                                                    ) : (
                                                        <div className="offerImageFallback">
                                                            Oferta
                                                        </div>
                                                    )}

                                                    <div>

                        <span>
                            {offer.source}
                        </span>

                                                        <strong>
                                                            {offer.title}
                                                        </strong>

                                                        {offer.detectedPrice !== undefined && (
                                                            <p className="offerPrice">
                                                                Około {offer.detectedPrice} zł
                                                            </p>
                                                        )}

                                                        {offer.opportunityScore !== undefined && (
                                                            <p className="offerScore">
                                                                Okazja: {offer.opportunityScore}/100
                                                            </p>
                                                        )}

                                                        {offer.badge && (
                                                            <div className="offerBadge">
                                                                {offer.badge}
                                                            </div>
                                                        )}

                                                        <p>
                                                            {offer.snippet}
                                                        </p>

                                                    </div>

                                                </a>
                                            )
                                        )}

                                    </div>

                                ) : (
                                    <>
                                        <p>
                                            Nie znaleziono konkretnych ofert.
                                            Możesz wyszukać ręcznie:
                                        </p>

                                        <div className="tags">

                                            {result.searchQueries?.map(
                                                (query, index) => (
                                                    <a
                                                        key={index}
                                                        className="tag"
                                                        href={`https://www.google.com/search?q=${encodeURIComponent(query)}`}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                    >
                                                        Szukaj: {query}
                                                    </a>
                                                )
                                            )}

                                        </div>
                                    </>
                                )}

                            </div>

                            <div className="bigCard">

                                <h3>
                                    Słowa kluczowe
                                </h3>

                                <div className="tags">

                                    {result.keywords?.map(
                                        (tag, index) => (
                                            <span
                                                key={index}
                                                className="tag"
                                            >
                                                {tag}
                                            </span>
                                        )
                                    )}

                                </div>

                            </div>

                        </>
                    )}

                </section>

            </section>

        </main>
    );
}

function InfoCard({
                      title,
                      value,
                  }: {
    title: string;
    value: string;
}) {
    return (
        <div className="infoCard">
            <span>{title}</span>
            <p>{value}</p>
        </div>
    );
}

export default App;