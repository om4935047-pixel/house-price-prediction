const API = window.location.origin;


// --------------------------------------------------
// FORMAT MONEY
// --------------------------------------------------

function money(value) {

    if (value === null || value === undefined) {
        return "₹0";
    }

    return "₹" + Number(value).toLocaleString("en-IN", {
        maximumFractionDigits: 0
    });
}


// --------------------------------------------------
// LOAD AREAS
// --------------------------------------------------

async function loadAreas() {

    try {

        const response =
            await fetch(`${API}/api/areas`);

        if (!response.ok) {
            throw new Error("API error");
        }

        const result =
            await response.json();

        const areaSelect =
            document.getElementById("area");

        const analysisSelect =
            document.getElementById("areaAnalysis");

        areaSelect.innerHTML =
            `<option value="">
                Select Area
            </option>`;

        analysisSelect.innerHTML =
            `<option value="">
                Select Area
            </option>`;

        result.areas.forEach(area => {

            const option1 =
                document.createElement("option");

            option1.value = area;
            option1.textContent = area;

            areaSelect.appendChild(option1);


            const option2 =
                document.createElement("option");

            option2.value = area;
            option2.textContent = area;

            analysisSelect.appendChild(option2);

        });

    } catch (error) {

        console.error(error);

        document.getElementById(
            "area"
        ).innerHTML =
            `<option>
                Backend not connected
            </option>`;
    }
}


// --------------------------------------------------
// PREDICT PRICE
// --------------------------------------------------

document
    .getElementById("predictionForm")
    .addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();

            const data = {

                area:
                    document.getElementById(
                        "area"
                    ).value,

                bhk:
                    document.getElementById(
                        "bhk"
                    ).value,

                bathrooms:
                    document.getElementById(
                        "bathrooms"
                    ).value,

                sqft:
                    document.getElementById(
                        "sqft"
                    ).value,

                age:
                    document.getElementById(
                        "age"
                    ).value
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
                                JSON.stringify(data)
                        }
                    );


                const result =
                    await response.json();


                if (!result.success) {

                    alert(
                        result.message
                    );

                    return;
                }


                document.getElementById(
                    "predictedPrice"
                ).textContent =
                    money(
                        result.predicted_price
                    );


                document.getElementById(
                    "minPrice"
                ).textContent =
                    money(
                        result.minimum_estimate
                    );


                document.getElementById(
                    "maxPrice"
                ).textContent =
                    money(
                        result.maximum_estimate
                    );


                document.getElementById(
                    "priceSqft"
                ).textContent =
                    money(
                        result.price_per_sqft
                    );


                document.getElementById(
                    "areaAverage"
                ).textContent =
                    money(
                        result.area_average_price
                    );


                document.getElementById(
                    "accuracy"
                ).textContent =
                    result.model_accuracy +
                    "%";


                document.getElementById(
                    "resultMessage"
                ).textContent =
                    `Estimated for ${result.area}, ${result.bhk} BHK property of ${result.sqft} sq.ft.`;

            } catch (error) {

                console.error(error);

                alert(
                    "Failed to fetch. Make sure the Flask server is running."
                );
            }

        }
    );


// --------------------------------------------------
// MARKET SUMMARY
// --------------------------------------------------

async function loadMarketSummary() {

    try {

        const response =
            await fetch(
                `${API}/api/market-summary`
            );

        const data =
            await response.json();


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
            money(
                data.average_price
            );


        document.getElementById(
            "averageSqft"
        ).textContent =
            money(
                data.average_price_per_sqft
            );

    } catch (error) {

        console.error(error);

    }
}


// --------------------------------------------------
// AREA CHART
// --------------------------------------------------

async function loadChart() {

    try {

        const response =
            await fetch(
                `${API}/api/area-stats`
            );

        const result =
            await response.json();


        const areas =
            result.data
                .slice(0, 10);


        const labels =
            areas.map(
                item => item.area
            );


        const prices =
            areas.map(
                item =>
                    item.average_price
            );


        new Chart(
            document.getElementById(
                "areaChart"
            ),
            {

                type: "bar",

                data: {

                    labels: labels,

                    datasets: [

                        {
                            label:
                                "Average Price",

                            data: prices
                        }

                    ]
                },

                options: {

                    responsive: true,

                    plugins: {

                        tooltip: {

                            callbacks: {

                                label:
                                    function(context) {

                                        return money(
                                            context.raw
                                        );

                                    }

                            }

                        }

                    },

                    scales: {

                        y: {

                            ticks: {

                                callback:
                                    function(value) {

                                        return money(
                                            value
                                        );

                                    }

                            }

                        }

                    }

                }

            }
        );

    } catch (error) {

        console.error(error);

    }
}


// --------------------------------------------------
// AREA DETAILS
// --------------------------------------------------

async function loadAreaDetails() {

    const area =
        document.getElementById(
            "areaAnalysis"
        ).value;


    if (!area) {

        alert(
            "Please select an area."
        );

        return;
    }


    try {

        const response =
            await fetch(
                `${API}/api/area/${encodeURIComponent(area)}`
            );


        const result =
            await response.json();


        if (!result.success) {

            alert(
                result.message
            );

            return;
        }


        document.getElementById(
            "detailAverage"
        ).textContent =
            money(
                result.average_price
            );


        document.getElementById(
            "detailSqft"
        ).textContent =
            money(
                result.price_per_sqft
            );


        document.getElementById(
            "detailMin"
        ).textContent =
            money(
                result.minimum_price
            );


        document.getElementById(
            "detailMax"
        ).textContent =
            money(
                result.maximum_price
            );

    } catch (error) {

        console.error(error);

        alert(
            "Could not load area information."
        );
    }
}


// --------------------------------------------------
// START
// --------------------------------------------------

document.addEventListener(
    "DOMContentLoaded",
    function() {

        loadAreas();

        loadMarketSummary();

        loadChart();

    }
);
