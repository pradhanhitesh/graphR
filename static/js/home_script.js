// Select DOM elements for the chat interface
const typingForm = document.querySelector(".typing-form");
const toogleThemeButton = document.querySelector("#toogle-theme-button");
const typingInput = document.querySelector(".typing-input");
const blurOverlay = document.getElementById("blur-overlay");
const popupModal = document.getElementById("popup-modal");
const invalidMsg = document.getElementById("invalid-message");
const validMsg = document.getElementById("valid-message");

function onSignIn(googleUser) {
    var profile = googleUser.getBasicProfile();
    console.log('ID: ' + profile.getId()); // Do not send to your backend! Use an ID token instead.
    console.log('Name: ' + profile.getName());
    console.log('Image URL: ' + profile.getImageUrl());
    console.log('Email: ' + profile.getEmail()); // This is null if the 'email' scope is not present.
}


// Toggle theme button functionality [Light/Dark Mode]
toogleThemeButton.addEventListener("click", () => {
    const isLightMode = document.body.classList.toggle("light_mode"); // Toggle light mode class
    localStorage.setItem("themeColor", isLightMode ? "light_mode" : "dark_mode");  // Store the current theme in localStorage
    toogleThemeButton.innerText = isLightMode ? "dark_mode" : "light_mode"; // Update button text
});

// Function to load saved chats and theme from localStorage
const loadLocalStorageDate = () => {
    // const savedChats = localStorage.getItem("savedChats");
    const isLightMode = (localStorage.getItem("themeColor") === "light_mode");

    // Toggle light mode class based on saved preference
    document.body.classList.toggle("light_mode", isLightMode);
    toogleThemeButton.innerText = isLightMode ? "dark_mode" : "light_mode";
}

// Load saved chats when the script runs
loadLocalStorageDate();

// Make the function async to use await
typingForm.addEventListener('submit', async (e) => {
    e.preventDefault(); // Prevent page refresh or default form action

    blurOverlay.style.display = "block";
    popupModal.style.display = "block";

    // Capture user input
    const userInput = typingInput.value;
    localStorage.setItem('userInput', userInput);

    try {
        // Send the link to the backend
        const response = await fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_link: userInput })
        });

        // Parse the JSON response
        const data = await response.json();

        // Redirect to the results page if the request is successful
        if (data.success) {
            window.location.href = `/profile/${data.result_id}`;
            localStorage.setItem('profileID', data.result_id);
        } else {
            console.error('Processing failed:', data.error);
            // Display the message
            validMsg.style.display = "none";
            invalidMsg.style.display = "block";
            
            setTimeout(function(){
                // Remove popup and blur
                blurOverlay.style.display = "none";
                popupModal.style.display = "none";
                validMsg.style.display = "block";
                invalidMsg.style.display = "none";
            }, 1500);

            
        }
    } catch (error) {
        console.error('Error while sending request:', error);
    }
});


// Page reloading
window.onpageshow = (event) => {
    if (event.persisted) {
        window.location.reload();
    }
};

window.onload = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const errorType = urlParams.get('error');
    const errorPopup = document.getElementById('errorPopup');
    const popupMessage = document.getElementById('popupMessage');

    // Define generic error messages
    const errorMessages = {
        'InternalNetworkError': 'Network error occurred. Please try again later.',
        'InternalServerError': 'Server error occurred. Please try again later.'
    };

    // Display the error popup if an error type is found in the URL
    if (errorType && errorMessages[errorType]) {
        popupMessage.textContent = errorMessages[errorType];
        errorPopup.style.display = 'flex';

        // Set a timeout to automatically hide the popup after 2 seconds
        setTimeout(() => {
            errorPopup.style.display = 'none';
        }, 2000);

        // Optionally, clear the error parameter from the URL
        history.replaceState(null, '', window.location.pathname);
    }
};