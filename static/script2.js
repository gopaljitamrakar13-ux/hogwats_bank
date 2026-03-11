// ================= SECTION NAVIGATION =================
function showSection(id) {
  document.querySelectorAll(".card").forEach((section) => {
    section.classList.add("hidden");
  });

  // Allow Create Account without login
  if (id === "create") {
    document.getElementById(id).classList.remove("hidden");
    return;
  }

  // Check login using backend session
  fetch("/user_details")
    .then((res) => {
      if (res.status === 401) {
        showPopup("Please login first ❌");
        throw new Error("Not logged in");
      }
      return res.json();
    })
    .then(() => {
      document.getElementById(id).classList.remove("hidden");

      if (id === "balance") loadBalance();
      if (id === "transactions") loadTransactions();
    })
    .catch(() => {});
}

// ================= CREATE ACCOUNT =================
function createAccount() {
  let name = document.getElementById("createName").value.trim();
  let email = document.getElementById("createEmail").value.trim();
  let password = document.getElementById("createPassword").value.trim();
  let phone = document.getElementById("createPhone").value.trim();
  let success = document.getElementById("createSuccess");

  if (!name || !email || !password || !phone) {
    success.innerHTML = "Please fill all fields";
    success.style.color = "red";
    return;
  }

  if (phone.length !== 10 || isNaN(phone)) {
    document.getElementById("createPhoneError").innerText =
      "Phone number must be 10 digits";
    return;
  } else {
    document.getElementById("createPhoneError").innerText = "";
  }

  fetch("/create_account", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password, phone }),
  })
    .then((res) => res.json())
    .then((data) => {
      success.innerHTML = data.message || data.error;
      success.style.color = data.success ? "green" : "red";

      if (data.success) {
        document.getElementById("createName").value = "";
        document.getElementById("createEmail").value = "";
        document.getElementById("createPassword").value = "";
        document.getElementById("createPhone").value = "";
      }
    });
}

// ================= LOGIN VALIDATION + LOGIN =================
function validateLogin() {
  let email = document.getElementById("loginEmail").value.trim();
  let password = document.getElementById("loginPassword").value.trim();
  let phone = document.getElementById("loginPhone").value.trim();

  let valid = true;

  // Email Validation
  if (!email.includes("@") || !email.includes(".")) {
    document.getElementById("loginEmailError").innerText = "Enter valid email";
    valid = false;
  } else {
    document.getElementById("loginEmailError").innerText = "";
  }

  // Password Validation
  if (password.length < 8) {
    document.getElementById("loginPasswordError").innerText =
      "Password must be at least 8 characters";
    valid = false;
  } else {
    document.getElementById("loginPasswordError").innerText = "";
  }

  // Phone Validation (UI only)
  if (phone.length !== 10 || isNaN(phone)) {
    document.getElementById("loginPhoneError").innerText =
      "Phone number must be 10 digits";
    valid = false;
  } else {
    document.getElementById("loginPhoneError").innerText = "";
  }

  if (!valid) return;

  // Real Login Call
  fetch("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        document.getElementById("loginSuccess").innerText = data.message;
        document.getElementById("loginBtn").innerText = "Logout";

        // Clear login fields
        document.getElementById("loginEmail").value = "";
        document.getElementById("loginPassword").value = "";
        document.getElementById("loginPhone").value = "";
        loadBalance();
        closeLoginModal();
        showSection("dashboard");
      } else {
        document.getElementById("loginPasswordError").innerText =
          "Invalid Credentials ❌";
      }
    });
}

// ================= LOGOUT / OPEN MODAL =================
function openLoginModal() {
  document.getElementById("loginModal").classList.remove("hidden");

  document.getElementById("loginEmail").value = "";
  document.getElementById("loginPassword").value = "";
  document.getElementById("loginPhone").value = "";
}

function closeLoginModal() {
  document.getElementById("loginModal").classList.add("hidden");

  // Clear login fields
  document.getElementById("loginEmail").value = "";
  document.getElementById("loginPassword").value = "";
  document.getElementById("loginPhone").value = "";

  // Clear error messages
  document.getElementById("loginEmailError").innerText = "";
  document.getElementById("loginPasswordError").innerText = "";
  document.getElementById("loginPhoneError").innerText = "";
}
function logoutUser() {
  fetch("/logout")
    .then((res) => res.json())
    .then(() => {
      document.getElementById("loginBtn").innerText = "Login";

      document.getElementById("welcomeUser").innerText = "Welcome";
      document.querySelector("#balance p").innerText =
        "Please login to view balance";

      showPopup("Logged Out Successfully ✅");
    });
}
function handleLoginButton() {
  let btn = document.getElementById("loginBtn");

  if (btn.innerText === "Login") {
    openLoginModal();
  } else {
    logoutUser();
  }
}

// ================= LOAD BALANCE =================

function loadBalance() {
  fetch("/user_details")
    .then((res) => {
      if (res.status === 401) {
        document.getElementById("welcomeUser").innerText = "Welcome";
        document.querySelector("#balance p").innerText =
          "Please login to view balance";
        return null;
      }
      return res.json();
    })
    .then((data) => {
      if (!data) return;

      document.getElementById("welcomeUser").innerText =
        "Welcome " + data.name + " 👋";

      document.querySelector("#balance p").innerText =
        "Your Current Balance: ₹" + data.balance;
    })
    .catch(() => {});
}

// ================= APPLY LOAN =================
function approveLoan() {
  let amount = document.getElementById("loanAmount").value;
  let result = document.getElementById("loanResult");

  if (!amount) {
    result.innerHTML = "Enter loan amount";
    result.style.color = "red";
    return;
  }

  fetch("/apply_loan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ amount }),
  })
    .then((res) => res.json())
    .then((data) => {
      result.innerHTML = data.message;

      // ✅ Clear the input after loan apply
      document.getElementById("loanAmount").value = "";
    });
}

// ================= TRANSFER MONEY =================
/*function transferMoney() {
  let amount = document.getElementById("transferAmount").value;
  let success = document.getElementById("transferSuccess");
  let error = document.getElementById("transferError");

  if (!amount) {
    error.innerHTML = "Enter valid amount";
    return;
  }

  fetch("/transfer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ amount }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.message.includes("Insufficient")) {
        error.innerHTML = data.message;
        success.innerHTML = "";
      } else {
        success.innerHTML = data.message;
        error.innerHTML = "";
        loadBalance();
      }
    });
}*/

function transferMoney() {
  let receiver = document.getElementById("receiverAccount").value.trim();
  let amount = document.getElementById("transferAmount").value;

  let success = document.getElementById("transferSuccess");
  let error = document.getElementById("transferError");

  if (receiver.length !== 12 || isNaN(receiver)) {
    document.getElementById("receiverError").innerText =
      "Account number must be 12 digits";
    return;
  } else {
    document.getElementById("receiverError").innerText = "";
  }

  if (!amount || amount <= 0) {
    error.innerText = "Enter valid amount";
    return;
  }

  fetch("/transfer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      receiver_account: receiver,
      amount: amount,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        success.innerText = data.message;
        error.innerText = "";

        document.getElementById("transferAmount").value = "";
        document.getElementById("receiverAccount").value = "";

        loadBalance();
      } else {
        error.innerText = data.message;
        success.innerText = "";
      }
    });
}
// ================= LOAD TRANSACTIONS =================
function loadTransactions() {
  fetch("/transactions")
    .then((res) => res.json())
    .then((data) => {
      let section = document.getElementById("transactions");
      section.innerHTML = "<h3>Transaction History</h3>";

      data.forEach((tx) => {
        let p = document.createElement("p");
        p.innerText =
          tx.type + " ₹" + tx.amount + " → Account " + tx.receiver_account;
        section.appendChild(p);
      });
    });
}

// ================= UPDATE PROFILE =================

function updateProfile() {
  let name = document.getElementById("updateName").value.trim();
  let email = document.getElementById("updateEmail").value.trim();
  let phone = document.getElementById("updatePhone").value.trim();
  let success = document.getElementById("profileSuccess");

  success.innerHTML = ""; // Clear old message

  // ✅ Validation
  if (name === "" || email === "" || phone === "") {
    success.innerHTML = "All fields are required!";
    success.style.color = "red";
    return;
  }

  if (phone.length !== 10 || isNaN(phone)) {
    success.innerHTML = "Phone number must be 10 digits!";
    success.style.color = "red";
    return;
  }

  fetch("/update_profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, phone }),
  })
    .then((res) =>
      res.json().then((data) => ({ status: res.status, body: data })),
    )
    .then(({ status, body }) => {
      success.innerHTML = body.message;

      if (status === 200) {
        success.style.color = "green";

        // Clear fields
        document.getElementById("updateName").value = "";
        document.getElementById("updateEmail").value = "";
        document.getElementById("updatePhone").value = "";
      } else {
        success.style.color = "red";
      }
    })
    .catch(() => {
      success.innerHTML = "Server error! Please try again.";
      success.style.color = "red";
    });
}

// ================= CHAT SECTION (UNCHANGED FEATURE) =================
function chatOption(type) {
  let response = document.getElementById("chatResponse");

  if (type === "emi") {
    response.innerText =
      "EMI(Equated Monthly Installment) means paying a big amount in small monthly payments.Instead of paying full money at once, you can pay a fixed amount every month. you can check our EMi calculator.";
  } else if (type === "transfer") {
    response.innerText =
      "Send money instantly, anytime, anywhere.Fast, secure, and reliable transfers.";
  } else if (type === "loan") {
    response.innerText =
      "Apply for instant loans from ₹5,000 to ₹50,000 with immediate approval. Loans above ₹50,000 are approved within 24 hours.";
  } else {
    response.innerText =
      "Contact us :- support@hogwartsbank.com | Phone No:- +91 XXXXXXXXX";
  }
}

// ================= EMI CALCULATOR =================
function calculateEMI() {
  let principal = parseFloat(document.getElementById("principal").value);
  let rate = parseFloat(document.getElementById("rate").value);
  let time = parseFloat(document.getElementById("time").value);
  let result = document.getElementById("emiResult");

  if (!principal || !rate || !time) {
    result.innerText = "Please fill all fields ❌";
    result.style.color = "red";
    return;
  }

  let monthlyRate = rate / 12 / 100;
  let months = time * 12;

  let emi =
    (principal * monthlyRate * Math.pow(1 + monthlyRate, months)) /
    (Math.pow(1 + monthlyRate, months) - 1);

  result.innerText = "Your EMI: ₹" + emi.toFixed(2);
  result.style.color = "green";
}

// ================= FORGOT PASSWORD =================
function forgotPassword() {
  document.getElementById("loginModal").classList.add("hidden");
  document.getElementById("forgotModal").classList.remove("hidden");
}

function closeForgotModal() {
  document.getElementById("forgotModal").classList.add("hidden");
}

function sendReset() {
  let email = document.getElementById("forgotEmail").value;
  let msg = document.getElementById("forgotMsg");

  fetch("/forgot_password", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email }),
  })
    .then((res) => res.json())
    .then((data) => {
      msg.innerText = data.message;
    });
}

// SHOW / HIDE PASSWORD
function togglePassword() {
  let pass = document.getElementById("loginPassword");
  let eye = document.querySelector(".eye-btn");

  if (pass.type === "password") {
    pass.type = "text";
    eye.classList.remove("fa-eye");
    eye.classList.add("fa-eye-slash");
  } else {
    pass.type = "password";
    eye.classList.remove("fa-eye-slash");
    eye.classList.add("fa-eye");
  }
}

function toggleSidebar() {
  let sidebar = document.querySelector(".sidebar");
  let main = document.querySelector(".main");

  sidebar.classList.toggle("active");
  main.classList.toggle("shift");
}

function showPopup(message) {
  let popup = document.getElementById("popupMsg");

  let text = document.getElementById("popupText");

  text.innerText = message;

  popup.classList.remove("hidden");

  setTimeout(() => {
    popup.classList.add("hidden");
  }, 3000);
}

// AUTO CLOSE SIDEBAR ON MOBILE AFTER CLICK

document.querySelectorAll(".sidebar ul li").forEach((item) => {
  item.addEventListener("click", function () {
    let sidebar = document.querySelector(".sidebar");
    let main = document.querySelector(".main");

    if (window.innerWidth <= 768) {
      sidebar.classList.remove("active");
      main.classList.remove("shift");
    }
  });
});
