document.addEventListener("DOMContentLoaded", function () {
    let currentStep = 1;
    const totalSteps = 3;
    
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    const submitBtn = document.getElementById("submitBtn");
    const progressBar = document.getElementById("progressBar");
    
    // Symptom cards click listener for visual feedback
    const symptomCards = document.querySelectorAll(".symptom-card-check");
    symptomCards.forEach(card => {
        const checkbox = card.querySelector("input[type='checkbox']");
        
        // If checked on load (e.g. back button), apply active class
        if (checkbox.checked) {
            card.classList.add("selected-active");
        }
        
        card.addEventListener("click", function (e) {
            // Prevent double trigger if clicking directly on the checkmark span/icon
            if (e.target.tagName !== "INPUT") {
                checkbox.checked = !checkbox.checked;
            }
            
            // Toggle visual class
            if (checkbox.checked) {
                card.classList.add("selected-active");
            } else {
                card.classList.remove("selected-active");
            }
            
            // Re-render summary if on step 3
            if (currentStep === 3) {
                updateSummary();
            }
        });
    });

    function showStep(step) {
        // Hide all steps
        for (let i = 1; i <= totalSteps; i++) {
            document.getElementById("step-" + i).classList.remove("active");
        }
        
        // Show active step
        document.getElementById("step-" + step).classList.add("active");
        
        // Update Buttons
        if (step === 1) {
            prevBtn.style.display = "none";
            nextBtn.style.display = "inline-block";
            submitBtn.style.display = "none";
        } else if (step === totalSteps) {
            prevBtn.style.display = "inline-block";
            nextBtn.style.display = "none";
            submitBtn.style.display = "inline-block";
            updateSummary();
        } else {
            prevBtn.style.display = "inline-block";
            nextBtn.style.display = "inline-block";
            submitBtn.style.display = "none";
        }
        
        // Update Progress Bar
        const percent = ((step - 1) / (totalSteps - 1)) * 100;
        progressBar.style.width = percent + "%";
        progressBar.setAttribute("aria-valuenow", percent);
    }
    
    function validateStep(step) {
        if (step === 1) {
            const name = document.getElementById("patient_name").value.trim();
            const age = document.getElementById("patient_age").value;
            const gender = document.querySelector("input[name='patient_gender']:checked");
            
            if (!name) {
                alert("Harap masukkan nama pasien.");
                return false;
            }
            if (!age || age <= 0 || age > 120) {
                alert("Harap masukkan umur pasien yang valid.");
                return false;
            }
            if (!gender) {
                alert("Harap pilih jenis kelamin pasien.");
                return false;
            }
            return true;
        }
        
        if (step === 2) {
            const checkedSymptoms = document.querySelectorAll("input[name='symptoms']:checked");
            if (checkedSymptoms.length === 0) {
                alert("Harap pilih minimal 1 gejala yang Anda rasakan.");
                return false;
            }
            return true;
        }
        
        return true;
    }
    
    function updateSummary() {
        const name = document.getElementById("patient_name").value.trim();
        const age = document.getElementById("patient_age").value;
        const genderVal = document.querySelector("input[name='patient_gender']:checked").value;
        const genderText = genderVal === "L" ? "Laki-laki" : "Perempuan";
        
        document.getElementById("summary-name").textContent = name;
        document.getElementById("summary-age").textContent = age + " Tahun";
        document.getElementById("summary-gender").textContent = genderText;
        
        // Gather selected symptoms
        const checkedSymptoms = document.querySelectorAll("input[name='symptoms']:checked");
        const listContainer = document.getElementById("summary-symptoms-list");
        listContainer.innerHTML = "";
        
        checkedSymptoms.forEach(checkbox => {
            const labelText = checkbox.closest(".symptom-card-check").querySelector(".symptom-name-text").textContent;
            const code = checkbox.value;
            
            const li = document.createElement("li");
            li.className = "list-group-item d-flex justify-content-between align-items-center py-2 border-0 ps-0 bg-transparent";
            li.innerHTML = `
                <span><i class="fa-solid fa-circle-dot text-primary me-2 fs-7"></i>${labelText}</span>
                <span class="badge bg-primary-subtle text-primary rounded-pill font-monospace small">Gejala</span>
            `;
            listContainer.appendChild(li);
        });
    }
    
    // Navigation Action Listeners
    nextBtn.addEventListener("click", function () {
        if (validateStep(currentStep)) {
            currentStep++;
            showStep(currentStep);
        }
    });
    
    prevBtn.addEventListener("click", function () {
        currentStep--;
        showStep(currentStep);
    });
    
    // Initialize step 1
    showStep(1);
});
