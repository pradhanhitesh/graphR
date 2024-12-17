const toogleThemeButton = document.getElementById("toogle-theme-button");
const searchButton = document.querySelector("#toogle-search-button");
const loadingIndicators = document.querySelectorAll(".loading-area");
const blurOverlay = document.getElementById("blur-overlay");
const popupModal = document.getElementById("popup-modal");
const textElement = document.getElementById("cycle-text");

let currentIndex = 0;
let userInput = localStorage.getItem('userInput');
let profileID = localStorage.getItem('profileID');

// Toggle theme button functionality [Light/Dark Mode]
toogleThemeButton.addEventListener("click", () => {
    const isLightMode = document.body.classList.toggle("light_mode"); // Toggle light mode class
    localStorage.setItem("themeColor", isLightMode ? "light_mode" : "dark_mode");  // Store the current theme in localStorage
    toogleThemeButton.innerText = isLightMode ? "dark_mode" : "light_mode"; // Update button text
});

// Function to update the URL based on button ID
function updateHref(buttonID) {
    const anchor = document.getElementById(buttonID);
    if (anchor) {
        let currentUrl = window.location.href; // Fetch the current page's URL

        // Replace the path "profile" with either "graph" or "email"
        if (buttonID === 'graph-network') {
            currentUrl = currentUrl.replace(/\/profile/, "/graph"); // Replace "/profile" with "/graph"
        } else {
            currentUrl = currentUrl.replace(/\/profile/, "/email"); // Replace "/profile" with "/email"
        }

        anchor.setAttribute("href", currentUrl); // Update the href attribute
    }
}


// Function to load saved chats and theme from localStorage
const loadLocalStorageDate = () => {
    const isLightMode = (localStorage.getItem("themeColor") === "light_mode");

    // Toggle light mode class based on saved preference
    document.body.classList.toggle("light_mode", isLightMode);
    toogleThemeButton.innerText = isLightMode ? "dark_mode" : "light_mode";
}

// // Load saved chats when the script runs
loadLocalStorageDate();

// Array of texts to cycle through
const texts = [
    "Searching articles on PubMed",
    "Extracting abstracts",
    "Thank you for your patience",
    "Building profile may take upto 60 seconds",
    "Do not close window or refresh the page"
];

// Function to cycle through texts
function cycleTexts() {
    // Update the text content
    textElement.textContent = texts[currentIndex];
    // Move to the next text in the array
    currentIndex = (currentIndex + 1) % texts.length;
}

// Start cycling every 1.5 seconds
setInterval(cycleTexts, 1500);

// Add click event listener to the search button
searchButton.addEventListener('click', () => {
    window.location.href = '/';
});

async function sendProfileLink(userInput) {
    const storedData = localStorage.getItem(profileID);

    if (storedData) {
        blurOverlay.style.display = "none";
        popupModal.style.display = "none";
        const data = JSON.parse(storedData);
        handleResponseData(data, true);
        
        // Add dynamic links to graph and email button
        updateHref("graph-network");
        updateHref("cold-email");
    } else {
        try {
            const response = await fetch('/scrap', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_link: userInput }),
            });

            // Redirect with a generic error if the response is not okay
            if (!response.ok) {
                console.error(`HTTP error! Status: ${response.status}`);
                window.location.href = '/?error=processError';
                return;
            }

            const data = await response.json();
            // Assuming the backend does not return a `message`, just check for success
            if (data.success) {
                localStorage.setItem(profileID, JSON.stringify(data));
                blurOverlay.style.display = "none";
                popupModal.style.display = "none";
                handleResponseData(data, false);

                // Add dynamic links to graph and email button
                updateHref("graph-network");
                updateHref("cold-email");
            } else {
                console.error('Request failed');
                console.log(data.message || 'No message available'); // Handle gracefully
                window.location.href = '/?error=dataFail';
            }
        } catch (error) {
            console.error('Error sending profile link:', error);
            window.location.href = '/?error=InternalServerError';
        }
    }
}


// Function to process the data (handle response)
function handleResponseData(data, fromLocalStorage = false) {
    // Extract values from JSON and store in an array
    const Text = Object.values(data); // Extract values from JSON and store in an array

    if (fromLocalStorage) {
        // If data is from localStorage, directly display the texts without typing effect
        Text.forEach((text, index) => {
            const loadingIndicator = loadingIndicators[index];
            loadingIndicator.innerHTML = text; // Directly set the text without typing effect
        });
    } else {
        // If data is not from localStorage, run the typing effect
        typeSections(0, Text); // Start typing effect with the first section
    }
}

// Function to handle typing effect for each section
function typeSections(index, texts) {
    if (index >= texts.length) return; // Stop if all sections are done

    // Select the loading indicator for the current section (Assuming you have a list of loadingIndicators)
    const loadingIndicator = loadingIndicators[index];
    const text = texts[index];

    // Set the typing effect for the current section
    typeEffect(loadingIndicator, text, 5, () => {
        // Once typing is complete, move to the next section
        setTimeout(() => {
            typeSections(index + 1, texts); // Move to the next section after a small delay
        }, 100); // 100ms delay before starting the next section
    });
}

// Function to create the typing effect
function typeEffect(element, text, speed, callback) {
    let index = 0;

    // Clear any existing content in the loading indicator
    element.innerHTML = '';

    // Create a typing effect by adding one character at a time
    const interval = setInterval(() => {
        element.innerHTML += text.charAt(index);
        index++;

        // Stop the interval when all the text has been typed
        if (index === text.length) {
            clearInterval(interval);
            if (callback) {
                callback(); // Execute the callback to start the next typing effect
            }
        }
    }, speed);
}

// Assuming `userInput` is defined and ready to be passed to the function
sendProfileLink(userInput);

document.getElementById('graph-network').addEventListener('click', function (event) {
    event.preventDefault(); // Prevent the default behavior

    const result_id = profileID; // Assuming this variable is defined elsewhere
    const icon = document.getElementById('graph-button'); // Get the icon element

    if (!result_id) {
        console.error('Result ID is missing or undefined.');
        return;
    }

    // Start icon rotation
    icon.classList.add('processing');

    // Retrieve the graphData object from localStorage
    const storedGraphData = JSON.parse(localStorage.getItem('graphData')) || {};

    // Check if data for the current result_id exists
    if (storedGraphData[result_id]) {
        console.log(`Graph data for result_id: ${result_id} found in localStorage. Skipping API request.`);
        
        // Stop icon rotation
        icon.classList.remove('processing');

        // Redirect to the next page directly
        window.location.href = `/graph/${result_id}`;
        return; // Exit the function
    }

    console.log(`No graph data found for result_id: ${result_id}. Sending API request.`);

    // Send a POST request to the /graph endpoint
    fetch('/graph', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ result_id: result_id }), // Send the result_id in the body
    })
        .then((response) => {
            if (response.ok) {
                return response.json(); // Assuming the server responds with JSON
            } else {
                throw new Error(`Request failed with status ${response.status}`);
            }
        })
        .then((data) => {
            console.log('Response data:', data); // Optionally log response data for debugging

            // Update the storedGraphData object with the new data
            storedGraphData[result_id] = data.response;

            // Save the updated graphData object back to localStorage
            localStorage.setItem('graphData', JSON.stringify(storedGraphData));
            localStorage.setItem('rawData', JSON.stringify(data.rawData));
            localStorage.setItem('communityData', JSON.stringify(data.communityData));

            // Redirect to the next page
            window.location.href = `/graph/${result_id}`;
        })
        .catch((error) => {
            console.error('Error fetching graph data:', error);
            alert('An error occurred while fetching the graph data. Please try again later.');
        })
        .finally(() => {
            // Stop icon rotation after fetch is complete
            icon.classList.remove('processing');
        });
});

document.getElementById("graph-network").addEventListener("click", function (e) {
    e.preventDefault(); // Prevent default link behavior
    const icon = document.getElementById("icon");
    icon.classList.add("processing");

    // Simulate a process with a timeout (e.g., replace this with actual process logic)
    setTimeout(() => {
        icon.classList.remove("processing");
    }, 5000); // Remove after 5 seconds
});
