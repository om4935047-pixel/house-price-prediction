// ============================================================
// HOUSEPRICE AI - MAIN JAVASCRIPT
// ============================================================

const API = window.location.origin;

// ============================================================
// GLOBAL VARIABLES
// ============================================================

let areaChart = null;
let trendChart = null;
let comparisonChart = null;
let distributionChart = null;

let allAreas = [];


// ============================================================
// DOM READY
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    initializeApp();

});


// ============================================================
// INITIALIZE APP
// ============================================================

async function initializeApp() {

    setupMobileMenu();

    setupSmoothScrolling();

    setupPredictionForm();

    setupAreaAnalysis();

    setupBudgetFinder();

    setupComparison();

    try {

        await loadAreas();

        await Promise.all([
            loadMarketSummary(),
            loadAreaChart(),
            loadRecommendations(),
            loadTrend(),
            loadDistribution()
        ]);

    } catch (error) {

        console.error(
            "Application initialization error:",
            error
        );

        showToast(
            "Some market data could not be loaded.",
            "error"
        );
    }
}


// ============================================================
// MOBILE MENU
// ============================================================

function setupMobileMenu() {

    const button =
        document.getElementById(
            "mobileMenuBtn"
        );

    const nav =
        document.querySelector(
            ".nav-links"
        );

    if (!button || !nav) return;

    button.addEventListener(
        "click",
        () => {

            nav.classList.toggle(
                "mobile-open"
            );

        }
    );


    nav.querySelectorAll("a").forEach(
        link => {

            link.addEventListener(
                "click",
                () => {

                    nav.classList.remove(
                        "mobile-open"
                    );

                }
            );

        }
    );
}


// ============================================================
// SMOOTH SCROLLING
// ============================================================

function setupSmoothScrolling() {

    document.querySelectorAll(
        'a[href^="#"]'
    ).forEach(link => {

        link.addEventListener(
            "click",
            function(event) {

                const targetId =
                    this.getAttribute(
                        "href"
                    );

                if (
                    !targetId ||
                    targetId === "#"
                ) {
                    return;
                }

                const target =
                    document.querySelector(
                        targetId
                    );

                if (!target) return;

                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }
        );

    });
}


// ============================================================
// API HELPER
// ============================================================

async function apiFetch(
    endpoint,
    options = {}
) {

    const response =
        await fetch(
            `${API}${endpoint}`,
            options
        );

    let data;

    try {

        data =
            await response.json();

    } catch {

        throw new Error(
            "Server returned an invalid response."
        );

    }

    if (!response.ok) {

        throw new Error(
            data.message ||
            "Something went wrong."
        );

    }

    return data;
}


// ============================================================
// LOAD AREAS
// ============================================================

async function loadAreas() {

    const result =
        await apiFetch(
            "/api/areas"
        );

    if (
        !result.success ||
        !Array.isArray(result.areas)
    ) {

        throw new Error(
            "Could not load areas."
        );

    }

    allAreas =
        result.areas;

    populateAreaSelects(
        allAreas
    );
}


// ============================================================
// POPULATE ALL AREA DROPDOWNS
// ============================================================

function populateAreaSelects(
    areas
) {

    const selectors = [

        document.getElementById(
            "area"
        ),

        document.getElementById(
            "areaAnalysis"
        ),

        document.getElementById(
            "compareArea1"
        ),

        document.getElementById(
            "compareArea2"
        ),

        document.getElementById(
            "compareArea3"
        )

    ];


    selectors.forEach(
        (select, index) => {

            if (!select) return;

            const firstOption =
                select.options[0];

            select.innerHTML = "";

            if (firstOption) {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    firstOption.value;

                option.textContent =
                    firstOption.textContent;

                select.appendChild(
                    option
                );
            }


            areas.forEach(
                area => {

                    const option =
                        document.createElement(
                            "option"
                        );

                    option.value =
                        area;

                    option.textContent =
                        area;

                    select.appendChild(
                        option
                    );

                }
            );

        }
    );
}


// ============================================================
// MARKET SUMMARY
// ============================================================

async function loadMarketSummary() {

    const result =
        await apiFetch(
            "/api/market-summary"
        );

    if (!result.success) return;


    setText(
        "totalProperties",
        formatNumber(
            result.total_properties
        )
    );

    setText(
        "totalAreas",
        formatNumber(
            result.total_areas
        )
    );

    setText(
        "averagePrice",
        formatCurrency(
            result.average_price
        )
    );

    setText(
        "averagePriceSqft",
        formatCurrency(
            result.average_price_per_sqft
        )
    );


    setText(
        "heroProperties",
        formatNumber(
            result.total_properties
        )
    );

    setText(
        "heroAreas",
        formatNumber(
            result.total_areas
        )
    );

    setText(
        "heroPriceSqft",
        formatCurrency(
            result.average_price_per_sqft
        )
    );


    const r2 =
        Number(
            result.model_r2 || 0
        );

    setText(
        "heroAccuracy",
        r2 > 0
            ? r2.toFixed(2)
            : "--"
    );
}


// ============================================================
// PREDICTION FORM
// ============================================================

function setupPredictionForm() {

    const form =
        document.getElementById(
            "predictionForm"
        );

    if (!form) return;


    form.addEventListener(
        "submit",
        async event => {

            event.preventDefault();

            await predictPrice();

        }
    );
}


// ============================================================
// PREDICT PRICE
// ============================================================

async function predictPrice() {

    const area =
        document.getElementById(
            "area"
        ).value;

    const bhk =
        document.getElementById(
            "bhk"
        ).value;

    const bathrooms =
        document.getElementById(
            "bathrooms"
        ).value;

    const sqft =
        document.getElementById(
            "sqft"
        ).value;

    const age =
        document.getElementById(
            "age"
        ).value;


    if (
        !area ||
        !bhk ||
        !bathrooms ||
        !sqft ||
        age === ""
    ) {

        showToast(
            "Please fill all property details.",
            "error"
        );

        return;
    }


    setPredictionLoading(
        true
    );


    try {

        const result =
            await apiFetch(
                "/api/predict",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        area: area,

                        bhk:
                            Number(bhk),

                        bathrooms:
                            Number(bathrooms),

                        sqft:
                            Number(sqft),

                        age:
                            Number(age)

                    })
                }
            );


        if (
            !result.success ||
            !result.prediction
        ) {

            throw new Error(
                result.message ||
                "Prediction failed."
            );

        }


        displayPrediction(
            result.prediction
        );


        // Update recommendations
        loadRecommendations(
            area
        );


        showToast(
            "House price predicted successfully!",
            "success"
        );


    } catch (error) {

        console.error(
            error
        );

        showToast(
            error.message ||
            "Prediction failed.",
            "error"
        );

    } finally {

        setPredictionLoading(
            false
        );
    }
}


// ============================================================
// DISPLAY PREDICTION
// ============================================================

function displayPrediction(
    prediction
) {

    setText(
        "predictedPrice",
        formatCurrency(
            prediction.price
        )
    );

    setText(
        "minimumPrice",
        formatCurrency(
            prediction.minimum
        )
    );

    setText(
        "maximumPrice",
        formatCurrency(
            prediction.maximum
        )
    );

    setText(
        "predictionPriceSqft",
        formatCurrency(
            prediction.price_per_sqft
        )
    );

    setText(
        "areaAverage",
        formatCurrency(
            prediction.area_average
        )
    );

    setText(
        "modelR2",
        Number(
            prediction.model_r2 || 0
        ).toFixed(2)
    );


    const progress =
        document.getElementById(
            "confidenceProgress"
        );

    if (progress) {

        let percentage =
            Number(
                prediction.model_r2 || 0
            ) * 100;

        percentage =
            Math.max(
                0,
                Math.min(
                    100,
                    percentage
                )
            );

        progress.style.width =
            `${percentage}%`;
    }


    const resultCard =
        document.getElementById(
            "predictionResult"
        );

    if (resultCard) {

        resultCard.classList.add(
            "result-active"
        );

        resultCard.scrollIntoView({
            behavior: "smooth",
            block: "nearest"
        });

    }
}


// ============================================================
// LOADING STATE
// ============================================================

function setPredictionLoading(
    loading
) {

    const buttonText =
        document.getElementById(
            "predictButtonText"
        );

    const loader =
        document.getElementById(
            "predictLoader"
        );


    if (buttonText) {

        buttonText.textContent =
            loading
                ? "Analyzing Property..."
                : "🔮 Predict House Price";

    }


    if (loader) {

        loader.classList.toggle(
            "hidden",
            !loading
        );

    }
}


// ============================================================
// AREA ANALYSIS
// ============================================================

function setupAreaAnalysis() {

    const select =
        document.getElementById(
            "areaAnalysis"
        );

    if (!select) return;


    select.addEventListener(
        "change",
        async () => {

            const area =
                select.value;

            if (!area) {

                showEmptyAreaState();

                return;
            }

            await loadAreaDetails(
                area
            );

            await loadRecommendations(
                area
            );

        }
    );
}


// ============================================================
// LOAD AREA DETAILS
// ============================================================

async function loadAreaDetails(
    area
) {

    try {

        const result =
            await apiFetch(
                `/api/area/${encodeURIComponent(area)}`
            );


        if (
            !result.success ||
            !result.data
        ) {

            throw new Error(
                "Area data unavailable."
            );

        }


        displayAreaDetails(
            result.data
        );


    } catch (error) {

        console.error(
            error
        );

        showToast(
            "Could not load area information.",
            "error"
        );
    }
}


// ============================================================
// DISPLAY AREA DETAILS
// ============================================================

function displayAreaDetails(
    data
) {

    const container =
        document.getElementById(
            "areaDetails"
        );

    if (!container) return;


    container.innerHTML = `

        <div class="selected-area">

            <div class="selected-area-icon">
                📍
            </div>

            <div>
                <span>Selected Area</span>

                <h3>
                    ${escapeHTML(data.area)}
                </h3>
            </div>

        </div>


        <div class="area-stat-grid">

            <div class="mini-stat">

                <span>
                    Average Price
                </span>

                <strong>
                    ${formatCurrency(
                        data.average_price
                    )}
                </strong>

            </div>


            <div class="mini-stat">

                <span>
                    Price / Sq.Ft.
                </span>

                <strong>
                    ${formatCurrency(
                        data.price_per_sqft
                    )}
                </strong>

            </div>


            <div class="mini-stat">

                <span>
                    Minimum
                </span>

                <strong>
                    ${formatCurrency(
                        data.minimum_price
                    )}
                </strong>

            </div>


            <div class="mini-stat">

                <span>
                    Maximum
                </span>

                <strong>
                    ${formatCurrency(
                        data.maximum_price
                    )}
                </strong>

            </div>

        </div>


        <div class="area-property-count">

            <span>
                🏘️ Properties available
            </span>

            <strong>
                ${formatNumber(
                    data.properties
                )}
            </strong>

        </div>

    `;
}


// ============================================================
// EMPTY AREA STATE
// ============================================================

function showEmptyAreaState() {

    const container =
        document.getElementById(
            "areaDetails"
        );

    if (!container) return;


    container.innerHTML = `

        <div class="empty-state">

            <span>📍</span>

            <p>
                Select an area to see
                detailed market information.
            </p>

        </div>

    `;
}


// ============================================================
// AREA CHART
// ============================================================

async function loadAreaChart() {

    try {

        const result =
            await apiFetch(
                "/api/area-stats"
            );


        if (
            !result.success ||
            !Array.isArray(result.data)
        ) {
            return;
        }


        const data =
            result.data;


        const labels =
            data.map(
                item => item.area
            );


        const values =
            data.map(
                item =>
                    item.average_price
            );


        const canvas =
            document.getElementById(
                "areaChart"
            );

        if (!canvas) return;


        if (areaChart) {

            areaChart.destroy();

        }


        areaChart =
            new Chart(
                canvas,
                {

                    type: "bar",

                    data: {

                        labels: labels,

                        datasets: [

                            {
                                label:
                                    "Average Property Price",

                                data:
                                    values,

                                borderWidth: 1,

                                borderRadius: 8

                            }

                        ]

                    },

                    options: {

                        responsive: true,

                        maintainAspectRatio: false,

                        plugins: {

                            legend: {
                                display: false
                            },

                            tooltip: {

                                callbacks: {

                                    label:
                                        context =>
                                            ` ${formatCurrency(
                                                context.raw
                                            )}`

                                }

                            }

                        },

                        scales: {

                            y: {

                                beginAtZero: true,

                                ticks: {

                                    callback:
                                        value =>
                                            formatCompactCurrency(
                                                value
                                            )

                                }

                            },

                            x: {

                                ticks: {

                                    maxRotation: 45,

                                    minRotation: 0

                                }

                            }

                        }

                    }

                }
            );

    } catch (error) {

        console.error(
            "Area chart error:",
            error
        );

    }
}


// ============================================================
// RECOMMENDATIONS
// ============================================================

async function loadRecommendations(
    area = ""
) {

    const grid =
        document.getElementById(
            "recommendationsGrid"
        );

    if (!grid) return;


    try {

        const endpoint =
            area
                ? `/api/recommendations?area=${encodeURIComponent(area)}`
                : "/api/recommendations";


        const result =
            await apiFetch(
                endpoint
            );


        if (
            !result.success ||
            !Array.isArray(result.data)
        ) {

            grid.innerHTML =
                `<div class="loading-card">
                    No recommendations available.
                </div>`;

            return;
        }


        if (result.data.length === 0) {

            grid.innerHTML =
                `<div class="loading-card">
                    No similar areas found.
                </div>`;

            return;
        }


        grid.innerHTML =
            result.data.map(
                (item, index) => `

                    <div class="recommendation-card">

                        <div class="recommendation-number">
                            ${String(
                                index + 1
                            ).padStart(
                                2,
                                "0"
                            )}
                        </div>

                        <div class="recommendation-content">

                            <div class="recommendation-title">

                                <span>
                                    📍
                                </span>

                                <h3>
                                    ${escapeHTML(
                                        item.area
                                    )}
                                </h3>

                            </div>


                            <div class="recommendation-info">

                                <div>

                                    <span>
                                        Average Price
                                    </span>

                                    <strong>
                                        ${formatCurrency(
                                            item.average_price
                                        )}
                                    </strong>

                                </div>


                                <div>

                                    <span>
                                        Price / Sq.Ft.
                                    </span>

                                    <strong>
                                        ${formatCurrency(
                                            item.price_per_sqft
                                        )}
                                    </strong>

                                </div>

                            </div>

                        </div>

                    </div>

                `
            ).join("");


    } catch (error) {

        console.error(
            "Recommendation error:",
            error
        );

        grid.innerHTML =
            `<div class="loading-card">
                Recommendations unavailable.
            </div>`;
    }
}


// ============================================================
// TREND CHART
// ============================================================

async function loadTrend() {

    const canvas =
        document.getElementById(
            "trendChart"
        );

    const empty =
        document.getElementById(
            "trendEmpty"
        );

    const message =
        document.getElementById(
            "trendMessage"
        );


    if (!canvas) return;


    try {

        const result =
            await apiFetch(
                "/api/trend"
            );


        if (
            !result.success ||
            !result.available ||
            !result.data ||
            result.data.length === 0
        ) {

            canvas.style.display =
                "none";

            if (empty) {

                empty.classList.remove(
                    "hidden"
                );

            }

            if (message) {

                message.textContent =
                    result.message ||
                    "Historical trend data is not available.";

            }

            return;
        }


        if (empty) {

            empty.classList.add(
                "hidden"
            );

        }


        canvas.style.display =
            "block";


        if (message) {

            message.textContent =
                "Average property price across available years.";

        }


        const labels =
            result.data.map(
                item =>
                    item.year
            );


        const values =
            result.data.map(
                item =>
                    item.average_price
            );


        if (trendChart) {

            trendChart.destroy();

        }


        trendChart =
            new Chart(
                canvas,
                {

                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [

                            {

                                label:
                                    "Average Property Price",

                                data:
                                    values,

                                fill: true,

                                tension: 0.35,

                                borderWidth: 3,

                                pointRadius: 5,

                                pointHoverRadius: 7

                            }

                        ]

                    },

                    options: {

                        responsive: true,

                        maintainAspectRatio: false,

                        plugins: {

                            legend: {
                                display: true
                            },

                            tooltip: {

                                callbacks: {

                                    label:
                                        context =>
                                            ` ${formatCurrency(
                                                context.raw
                                            )}`

                                }

                            }

                        },

                        scales: {

                            y: {

                                beginAtZero: false,

                                ticks: {

                                    callback:
                                        value =>
                                            formatCompactCurrency(
                                                value
                                            )

                                }

                            }

                        }

                    }

                }
            );


    } catch (error) {

        console.error(
            "Trend error:",
            error
        );

    }
}


// ============================================================
// BUDGET FINDER
// ============================================================

function setupBudgetFinder() {

    const button =
        document.getElementById(
            "budgetBtn"
        );

    if (!button) return;


    button.addEventListener(
        "click",
        findBudgetAreas
    );
}


async function findBudgetAreas() {

    const input =
        document.getElementById(
            "budget"
        );

    const results =
        document.getElementById(
            "budgetResults"
        );


    if (!input || !results) return;


    const budget =
        Number(
            input.value
        );


    if (
        !budget ||
        budget <= 0
    ) {

        showToast(
            "Enter a valid budget.",
            "error"
        );

        return;
    }


    results.innerHTML =
        `<div class="loading-card">
            Searching suitable areas...
        </div>`;


    try {

        const result =
            await apiFetch(
                `/api/budget?budget=${encodeURIComponent(
                    budget
                )}`
            );


        if (
            !result.success ||
            !result.data
        ) {

            throw new Error(
                result.message ||
                "Could not search areas."
            );

        }


        if (
            result.data.length === 0
        ) {

            results.innerHTML =
                `<div class="no-results">
                    <span>🔍</span>
                    <h3>No matching areas found</h3>
                    <p>
                        Try increasing your budget
                        or checking the market data.
                    </p>
                </div>`;

            return;
        }


        results.innerHTML =
            result.data.map(
                item => `

                    <div class="budget-result-card">

                        <div class="budget-result-icon">
                            📍
                        </div>

                        <div>

                            <h3>
                                ${escapeHTML(
                                    item.area
                                )}
                            </h3>

                            <span>
                                Average:
                                ${formatCurrency(
                                    item.average_price
                                )}
                            </span>

                        </div>

                        <strong>
                            ${formatCurrency(
                                item.price_per_sqft
                            )}
                            /sq.ft.
                        </strong>

                    </div>

                `
            ).join("");


        showToast(
            `${result.data.length} area(s) found.`,
            "success"
        );


    } catch (error) {

        console.error(
            error
        );

        results.innerHTML =
            `<div class="no-results">
                <span>⚠️</span>
                <h3>Search failed</h3>
                <p>
                    ${escapeHTML(
                        error.message
                    )}
                </p>
            </div>`;
    }
}


// ============================================================
// AREA COMPARISON
// ============================================================

function setupComparison() {

    const button =
        document.getElementById(
            "compareBtn"
        );

    if (!button) return;


    button.addEventListener(
        "click",
        compareAreas
    );
}


async function compareAreas() {

    const ids = [

        "compareArea1",

        "compareArea2",

        "compareArea3"

    ];


    const selected =
        ids
            .map(
                id =>
                    document.getElementById(
                        id
                    )?.value
            )
            .filter(Boolean);


    const uniqueAreas =
        [...new Set(selected)];


    if (
        uniqueAreas.length < 2
    ) {

        showToast(
            "Select at least 2 different areas.",
            "error"
        );

        return;
    }


    try {

        const result =
            await apiFetch(
                `/api/compare?areas=${encodeURIComponent(
                    uniqueAreas.join(",")
                )}`
            );


        if (
            !result.success ||
            !result.data
        ) {

            throw new Error(
                result.message ||
                "Comparison failed."
            );

        }


        displayComparison(
            result.data
        );


    } catch (error) {

        console.error(
            error
        );

        showToast(
            error.message ||
            "Comparison failed.",
            "error"
        );
    }
}


// ============================================================
// DISPLAY COMPARISON
// ============================================================

function displayComparison(
    data
) {

    const container =
        document.getElementById(
            "comparisonResults"
        );

    const chartContainer =
        document.getElementById(
            "comparisonChartContainer"
        );


    if (!container) return;


    container.innerHTML =
        data.map(
            item => `

                <div class="comparison-card">

                    <div class="comparison-card-header">

                        <span>
                            📍
                        </span>

                        <h3>
                            ${escapeHTML(
                                item.area
                            )}
                        </h3>

                    </div>


                    <div class="comparison-stat">

                        <span>
                            Average Price
                        </span>

                        <strong>
                            ${formatCurrency(
                                item.average_price
                            )}
                        </strong>

                    </div>


                    <div class="comparison-stat">

                        <span>
                            Price / Sq.Ft.
                        </span>

                        <strong>
                            ${formatCurrency(
                                item.price_per_sqft
                            )}
                        </strong>

                    </div>


                    <div class="comparison-stat">

                        <span>
                            Properties
                        </span>

                        <strong>
                            ${formatNumber(
                                item.properties
                            )}
                        </strong>

                    </div>

                </div>

            `
        ).join("");


    if (
        chartContainer
    ) {

        chartContainer.classList.remove(
            "hidden"
        );

    }


    const canvas =
        document.getElementById(
            "comparisonChart"
        );

    if (!canvas) return;


    if (comparisonChart) {

        comparisonChart.destroy();

    }


    comparisonChart =
        new Chart(
            canvas,
            {

                type: "bar",

                data: {

                    labels:
                        data.map(
                            item =>
                                item.area
                        ),

                    datasets: [

                        {

                            label:
                                "Average Price",

                            data:
                                data.map(
                                    item =>
                                        item.average_price
                                ),

                            borderRadius: 8,

                            borderWidth: 1

                        },

                        {

                            label:
                                "Price / Sq.Ft.",

                            data:
                                data.map(
                                    item =>
                                        item.price_per_sqft
                                ),

                            borderRadius: 8,

                            borderWidth: 1

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        tooltip: {

                            callbacks: {

                                label:
                                    context =>
                                        ` ${formatCurrency(
                                            context.raw
                                        )}`

                            }

                        }

                    },

                    scales: {

                        y: {

                            beginAtZero: true,

                            ticks: {

                                callback:
                                    value =>
                                        formatCompactCurrency(
                                            value
                                        )

                            }

                        }

                    }

                }

            }
        );
}


// ============================================================
// PRICE DISTRIBUTION
// ============================================================

async function loadDistribution() {

    const canvas =
        document.getElementById(
            "distributionChart"
        );

    if (!canvas) return;


    try {

        const result =
            await apiFetch(
                "/api/price-distribution"
            );


        if (
            !result.success ||
            !result.data
        ) return;


        const labels =
            result.data.map(
                item =>
                    `${formatCompactCurrency(
                        item.minimum
                    )} - ${formatCompactCurrency(
                        item.maximum
                    )}`
            );


        const values =
            result.data.map(
                item =>
                    item.count
            );


        if (distributionChart) {

            distributionChart.destroy();

        }


        distributionChart =
            new Chart(
                canvas,
                {

                    type: "bar",

                    data: {

                        labels: labels,

                        datasets: [

                            {

                                label:
                                    "Number of Properties",

                                data:
                                    values,

                                borderRadius: 8,

                                borderWidth: 1

                            }

                        ]

                    },

                    options: {

                        responsive: true,

                        maintainAspectRatio: false,

                        plugins: {

                            legend: {
                                display: false
                            }

                        },

                        scales: {

                            y: {

                                beginAtZero: true,

                                ticks: {

                                    precision: 0

                                }

                            },

                            x: {

                                ticks: {

                                    maxRotation: 45,

                                    minRotation: 20

                                }

                            }

                        }

                    }

                }
            );


    } catch (error) {

        console.error(
            "Distribution error:",
            error
        );

    }
}


// ============================================================
// TEXT HELPER
// ============================================================

function setText(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );

    if (element) {

        element.textContent =
            value;

    }
}


// ============================================================
// NUMBER FORMAT
// ============================================================

function formatNumber(
    value
) {

    const number =
        Number(value);

    if (
        Number.isNaN(number)
    ) {
        return "--";
    }

    return new Intl.NumberFormat(
        "en-IN"
    ).format(number);
}


// ============================================================
// CURRENCY FORMAT
// ============================================================

function formatCurrency(
    value
) {

    const number =
        Number(value);

    if (
        Number.isNaN(number)
    ) {
        return "₹ --";
    }

    return (
        "₹ " +
        new Intl.NumberFormat(
            "en-IN",
            {
                maximumFractionDigits: 0
            }
        ).format(number)
    );
}


// ============================================================
// COMPACT CURRENCY
// ============================================================

function formatCompactCurrency(
    value
) {

    const number =
        Number(value);

    if (
        Number.isNaN(number)
    ) {
        return "₹ --";
    }


    if (
        Math.abs(number) >= 10000000
    ) {

        return (
            "₹ " +
            (
                number / 10000000
            ).toFixed(1) +
            " Cr"
        );

    }


    if (
        Math.abs(number) >= 100000
    ) {

        return (
            "₹ " +
            (
                number / 100000
            ).toFixed(1) +
            " L"
        );

    }


    if (
        Math.abs(number) >= 1000
    ) {

        return (
            "₹ " +
            (
                number / 1000
            ).toFixed(0) +
            "K"
        );

    }


    return formatCurrency(
        number
    );
}


// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHTML(
    value
) {

    return String(
        value ?? ""
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


// ============================================================
// TOAST
// ============================================================

function showToast(
    message,
    type = "success"
) {

    const toast =
        document.getElementById(
            "toast"
        );

    const toastMessage =
        document.getElementById(
            "toastMessage"
        );

    const toastIcon =
        document.getElementById(
            "toastIcon"
        );


    if (
        !toast ||
        !toastMessage
    ) return;


    toastMessage.textContent =
        message;


    toast.classList.remove(
        "success",
        "error",
        "show"
    );


    if (
        type === "error"
    ) {

        toast.classList.add(
            "error"
        );

        if (toastIcon) {

            toastIcon.textContent =
                "!";
        }

    } else {

        toast.classList.add(
            "success"
        );

        if (toastIcon) {

            toastIcon.textContent =
                "✓";
        }
    }


    // Trigger animation
    requestAnimationFrame(
        () => {

            toast.classList.add(
                "show"
            );

        }
    );


    clearTimeout(
        window.toastTimer
    );


    window.toastTimer =
        setTimeout(
            () => {

                toast.classList.remove(
                    "show"
                );

            },
            3500
        );
}


// ============================================================
// CONSOLE INFO
// ============================================================

console.log(
    "🏠 HousePrice AI loaded successfully."
);
