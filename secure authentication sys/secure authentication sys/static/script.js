const authSection = document.getElementById("auth-section");

const dashboard = document.getElementById("dashboard");

const messageBox = document.getElementById("message");


function showMessage(text, type = "success") {

    messageBox.textContent = text;

    messageBox.className = `message ${type}`;

    setTimeout(() => {

        messageBox.className = "message hidden";

    }, 5000);
}


// Registration

async function registerUser(event) {

    event.preventDefault();

    const username =
        document.getElementById("register-username").value.trim();

    const email =
        document.getElementById("register-email").value.trim();

    const password =
        document.getElementById("register-password").value;


    try {

        const response = await fetch("/api/register", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                username,
                email,
                password
            })
        });


        const data = await response.json();


        if (!response.ok) {
            throw new Error(
                data.message || "Registration failed."
            );
        }


        showMessage(
            data.message,
            "success"
        );


        document
            .getElementById("register-form")
            .reset();


    } catch (error) {

        showMessage(
            error.message,
            "error"
        );

    }
}


// Login

async function loginUser(event) {

    event.preventDefault();


    const email =
        document.getElementById("login-email").value.trim();

    const password =
        document.getElementById("login-password").value;


    try {

        const response = await fetch("/api/login", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                email,
                password
            })
        });


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.message || "Login failed."
            );

        }


        // Store token for this browser session
        sessionStorage.setItem(
            "jwt_token",
            data.token
        );


        document
            .getElementById("login-form")
            .reset();


        showMessage(
            data.message,
            "success"
        );


        await loadProfile();


    } catch (error) {

        showMessage(
            error.message,
            "error"
        );

    }
}


// Load protected profile

async function loadProfile() {

    const token =
        sessionStorage.getItem("jwt_token");


    if (!token) {

        showAuth();

        return;

    }


    try {

        const response = await fetch(
            "/api/profile",
            {
                method: "GET",

                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );


        const data = await response.json();


        if (!response.ok) {

            sessionStorage.removeItem(
                "jwt_token"
            );

            throw new Error(
                data.message ||
                "Unable to load profile."
            );

        }


        document.getElementById(
            "profile-id"
        ).textContent = data.user.id;


        document.getElementById(
            "profile-username"
        ).textContent = data.user.username;


        document.getElementById(
            "profile-email"
        ).textContent = data.user.email;


        authSection.classList.add(
            "hidden"
        );

        dashboard.classList.remove(
            "hidden"
        );


    } catch (error) {

        showAuth();

        showMessage(
            error.message,
            "error"
        );

    }
}


// Show login/register forms

function showAuth() {

    authSection.classList.remove(
        "hidden"
    );

    dashboard.classList.add(
        "hidden"
    );
}


// Logout

function logoutUser() {

    sessionStorage.removeItem(
        "jwt_token"
    );


    document.getElementById(
        "profile-id"
    ).textContent = "-";


    document.getElementById(
        "profile-username"
    ).textContent = "-";


    document.getElementById(
        "profile-email"
    ).textContent = "-";


    showAuth();


    showMessage(
        "You have been logged out.",
        "success"
    );
}


// Event listeners

document
    .getElementById("register-form")
    .addEventListener(
        "submit",
        registerUser
    );


document
    .getElementById("login-form")
    .addEventListener(
        "submit",
        loginUser
    );


document
    .getElementById("logout-btn")
    .addEventListener(
        "click",
        logoutUser
    );


// Check login when page loads

window.addEventListener(
    "load",
    loadProfile
);