const API = window.location.origin;

let areaChart = null;


// =====================================================
// HELPERS
// =====================================================

function money(value) {

    if (
        value === null ||
        value === undefined ||
        isNaN(value)
    ) {
        return "₹ —";
    }

    return "₹ " + Number(value).toLocaleString("en-IN", {
        maximumFractionDigits: 0
    });
}


function showError(message) {

    const error = document.getElementById("error");

    if (error) {
        error.textContent = message;
    }
}


function clearError() {

    const error = document.getElementById("error");

    if (error) {
        error.textContent = "";
    }
}


// =====================================================
// API HEALTH
// =====================================================

async function checkAPI() {

    const status =
        document.getElementById("apiStatus");

    try {

        const response =
            await fetch(`${API}/api/health`);

        const data =
            await response.json();

        if (data.success) {

            status.textContent =
                "● API Connected";

            status.classList.add("online");

        } else {

            status.textContent =
                "● API Error";
        }

    } catch (error) {

        status.textContent =
            "● Backend Offline";

        status.classList.add("offline");
    }
}


// =====================================================
// LOAD LOCATIONS
// =====================================================

async function loadLocations() {

    try {

        const response =
            await fetch(`${API}/api/locations`);

        const data =
            await response.json();


        if (!data.success) {
            throw new Error(
                "Could not load locations"
            );
        }


        const stateSelect =
            document.getElementById("state");

        const citySelect =
            document.getElementById("city");

        const areaSelect =
            document.getElementById("area");


        // STATES

        stateSelect.innerHTML =
            `<option value="">Select State</option>`;

        data.states.forEach(state => {

            const option =
                document.createElement("option");

            option.value = state;
            option.textContent = state;

            stateSelect.appendChild(option);
        });


        // CITIES

        citySelect.innerHTML =
            `<option value="">Select City</option>`;

        data.cities.forEach(city => {

            const option =
                document.createElement("option");

            option.value = city;
            option.textContent = city;

            citySelect.appendChild(option);
        });


        // AREAS

        areaSelect.innerHTML =
            `<option value="">Select Area</option>`;

        data.areas.forEach(area => {

            const option =
                document.createElement("option");

            option.value = area;
            option.textContent = area;

            areaSelect.appendChild(option);
        });

    } catch (error) {

        console.error(
            "Location error:",
            error
        );

        document.getElementById(
            "area"
        ).innerHTML =
            `<option value="">Unable to load areas</option>`;
    }
}


// =====================================================
// STATE CHANGE
// =====================================================

async function stateChanged() {

    const state =
        document.getElementById("state").value;

    const citySelect =
        document.getElementById("city");

    const areaSelect =
        document.getElementById("area");


    citySelect.innerHTML =
        `<option value="">Loading cities...</option>`;

    areaSelect.innerHTML =
        `<option value="">Select Area</option>`;


    try {

        const url =
            `${API}/api/cities?state=${encodeURIComponent(state)}`;

        const response =
            await fetch(url);

        const data =
            await response.json();


        citySelect.innerHTML =
            `<option value="">Select City</option>`;


        data.cities.forEach(city => {

            const option =
                document.createElement("option");

            option.value = city;
            option.textContent = city;

            citySelect.appendChild(option);
        });


        await loadFilteredAreas();

    } catch (error) {

        console.error(error);
    }
}


// =====================================================
// CITY CHANGE
// =====================================================

async function cityChanged() {

    await loadFilteredAreas();
}


// =====================================================
// FILTER AREAS
// =====================================================

async function loadFilteredAreas() {

    const state =
        document.getElementById("state").value;

    const city =
        document.getElementById("city").value;

    const areaSelect =
        document.getElementById("area");


    areaSelect.innerHTML =
        `<option value="">Loading areas...</option>`;


    try {

        const params =
            new URLSearchParams();


        if (state) {
            params.append(
                "state",
                state
            );
        }


        if (city) {
            params.append(
                "city",
                city
            );
        }


        const response =
            await fetch(
                `${API}/api/filter-areas?${params}`
            );


        const data =
            await response.json();


        areaSelect.innerHTML =
            `<option value="">Select Area</option>`;


        data.areas.forEach(area => {

            const option =
                document.createElement("option");

            option.value = area;
            option.textContent = area;

            areaSelect.appendChild(option);
        });


    } catch (error) {

        console.error(error);

        areaSelect.innerHTML =
            `<option value="">Unable to load areas</option>`;
    }
}


// =====================================================
// PREDICTION
// =====================================================

async function predictPrice(event) {

    event.preventDefault();

    clearError();


    const button =
        document.querySelector(
            "#predictForm button"
        );

    button.disabled = true;

    button.textContent =
        "Calculating...";


    const payload = {

        area:
            document.getElementById(
                "area"
            ).value,

        bhk:
            Number(
                document.getElementById(
                    "bhk"
                ).value
            ),

        bathrooms:
            Number(
                document.getElementById(
                    "bathrooms"
                ).value
            ),

        sqft:
            Number(
                document.getElementById(
                    "sqft"
                ).value
            ),

        age:
            Number(
                document.getElementById(
                    "age"
                ).value
            )
    };


    try {

        const response =
            await fetch(
                `${API}/api/predict`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(payload)
                }
            );


        const data =
            await response.json();


        if (!response.ok || !data.success) {

            throw new Error(
                data.message ||
                "Prediction failed"
            );
        }


        displayPrediction(
            data
        );


    } catch (error) {

        console.error(
            "Prediction error:",
            error
        );

        showError(
            error.message
        );

    } finally {

        button.disabled = false;

        button.textContent =
            "Calculate Property Value";
    }
}


// =====================================================
// DISPLAY PREDICTION
// =====================================================

function displayPrediction(data) {

    const result =
        document.getElementById(
            "result"
        );


    result.innerHTML = `

        <div class="result-content">

            <div class="result-label">
                ESTIMATED PROPERTY VALUE
            </div>

            <div class="price">
                ${money(data.predicted_price)}
            </div>

            <p class="result-area">
                ${data.area}
            </p>


            <div class="estimate-range">

                <div>
                    <span>Minimum</span>
                    <strong>
                        ${money(data.minimum_estimate)}
                    </strong>
                </div>

                <div>
                    <span>Maximum</span>
                    <strong>
                        ${money(data.maximum_estimate)}
                    </strong>
                </div>

            </div>


            <div class="result-details">

                <div>
                    <span>Price / sq ft</span>
                    <strong>
                        ₹${Number(
                            data.price_per_sqft
                        ).toLocaleString("en-IN")}
                    </strong>
                </div>


                <div>
                    <span>Area Average</span>
                    <strong>
                        ${money(
                            data.area_average_price
                        )}
                    </strong>
                </div>


                <div>
                    <span>Model Accuracy</span>
                    <strong>
                        ${data.model_accuracy}%
                    </strong>
                </div>


                <div>
                    <span>MAE</span>
                    <strong>
                        ${money(data.mae)}
                    </strong>
                </div>

            </div>

        </div>
    `;
}


// =====================================================
// MARKET SUMMARY
// =====================================================

async function loadMarketSummary() {

    try {

        const response =
            await fetch(
                `${API}/api/market-summary`
            );

        const data =
            await response.json();


        if (!data.success) {
            return;
        }


        document.getElementById(
            "totalProperties"
        ).textContent =
            data.total_properties;


        document.getElementById(
            "totalAreas"
        ).textContent =
            data.total_areas;


        document.getElementById(
            "averagePrice"
        ).textContent =
            money(data.average_price);


        document.getElementById(
            "averagePps"
        ).textContent =
            "₹" +
            Number(
                data.average_price_per_sqft
            ).toLocaleString("en-IN");

    } catch (error) {

        console.error(
            "Market error:",
            error
        );
    }
}


// =====================================================
// AREA CHART
// =====================================================

async function loadAreaChart() {

    try {

        const response =
            await fetch(
                `${API}/api/area-stats`
            );

        const result =
            await response.json();


        if (!result.success) {
            return;
        }


        const rows =
            result.data.slice(0, 15);


        const labels =
            rows.map(
                row => row.area
            );


        const values =
            rows.map(
                row => row.average_price
            );


        const canvas =
            document.getElementById(
                "areaChart"
            );


        if (areaChart) {
            areaChart.destroy();
        }


        areaChart =
            new Chart(
                canvas,
                {
                    type: "bar",

                    data: {

                        labels,

                        datasets: [
                            {
                                label:
                                    "Average Price",

                                data:
                                    values,

                                borderRadius: 8
                            }
                        ]
                    },

                    options: {

                        responsive: true,

                        maintainAspectRatio:
                            false,

                        plugins: {

                            legend: {
                                display: false
                            }

                        },

                        scales: {

                            y: {

                                beginAtZero:
                                    true,

                                ticks: {

                                    callback:
                                        function(value) {

                                            return "₹" +
                                                Number(
                                                    value
                                                ).toLocaleString(
                                                    "en-IN"
                                                );
                                        }
                                }
                            }

                        }
                    }
                }
            );

    } catch (error) {

        console.error(
            "Chart error:",
            error
        );
    }
}


// =====================================================
// RECOMMENDATIONS
// =====================================================

async function loadRecommendations() {

    const container =
        document.getElementById(
            "recommendations"
        );


    try {

        const response =
            await fetch(
                `${API}/api/recommendations`
            );

        const result =
            await response.json();


        if (
            !result.success ||
            !result.data.length
        ) {

            container.innerHTML =
                "<p>No area data available.</p>";

            return;
        }


        container.innerHTML =
            result.data.map(
                item => `

                <div class="recommendation-card">

                    <div class="recommendation-top">

                        <span>
                            ${item.area}
                        </span>

                        <span class="area-badge">
                            Value
                        </span>

                    </div>

                    <h3>
                        ${money(
                            item.average_price
                        )}
                    </h3>

                    <p>
                        ₹${Number(
                            item.price_per_sqft
                        ).toLocaleString(
                            "en-IN"
                        )} / sq ft
                    </p>

                    <small>
                        ${item.properties}
                        properties in dataset
                    </small>

                </div>
            `
            ).join("");

    } catch (error) {

        console.error(
            "Recommendation error:",
            error
        );

        container.innerHTML =
            "<p>Unable to load area insights.</p>";
    }
}


// =====================================================
// EVENTS
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        checkAPI();

        await loadLocations();

        loadMarketSummary();

        loadAreaChart();

        loadRecommendations();


        document
            .getElementById("state")
            .addEventListener(
                "change",
                stateChanged
            );


        document
            .getElementById("city")
            .addEventListener(
                "change",
                cityChanged
            );


        document
            .getElementById("predictForm")
            .addEventListener(
                "submit",
                predictPrice
            );
    }
);
