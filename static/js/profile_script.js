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

// Function to send the link to the backend or get from local storage
async function sendProfileLink(userInput) {
    const storedData = localStorage.getItem(profileID);
    
    if (storedData) {
        blurOverlay.style.display = "none";
        popupModal.style.display = "none";
        const data = JSON.parse(storedData);
        handleResponseData(data, true);
    } else {
        try {
            const response = await fetch('/process_1', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_link: userInput })
            });

            // Redirect with a generic error if the response is not okay
            if (!response.ok) {
                console.error(`HTTP error! Status: ${response.status}`);
                window.location.href = '/?error=InternalNetworkError';
                return;
            }

            const data = await response.json();

            // Assuming the backend does not return a `message`, just check for success
            if (data.success) {
                localStorage.setItem(profileID, JSON.stringify(data));
                blurOverlay.style.display = "none";
                popupModal.style.display = "none";
                handleResponseData(data, false);
            } else {
                console.error('Request failed');
                window.location.href = '/?error=InternalServerError';
                console.log(data.message);
            }
        } catch (error) {
            console.error('Error sending profile link:', error);
            window.location.href = '/?error=InternalServerError';
            console.log(data.message);
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