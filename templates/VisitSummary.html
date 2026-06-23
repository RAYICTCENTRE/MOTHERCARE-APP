<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>MotherCare – Client Visit Summary</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(to right, #e3f2fd, #fce4ec);
    margin: 0;
    padding: 20px;
  }
  .summary-container {
    max-width: 900px;
    background: white;
    margin: 40px auto;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
  }
  h1, h2 { text-align: center; color: #6a1b9a; margin-bottom: 10px; }
  .card {
    background-color: #81c784;
    color: white;
    padding: 12px 16px;
    margin: 10px 0;
    border-radius: 8px;
    font-weight: 600;
  }
  .card.moderate { background-color: #ffb74d; color: black; }
  .card.high { background-color: #e57373; color: white; }
  #profile-toggle {
    display: block;
    margin: 20px auto;
    padding: 10px 25px;
    background-color: #6a1b9a;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1rem;
  }
  #profile-details {
    display: none;
    background-color: #f3e5f5;
    border-left: 5px solid #ab47bc;
    padding: 15px 20px;
    margin-bottom: 20px;
    border-radius: 8px;
    color: #4a148c;
  }
  canvas { display: block; margin: 30px auto 10px auto; max-width: 100%; }
  .download-btn, .dashboard-btn {
    display: block;
    margin: 10px auto;
    padding: 12px 30px;
    border: none;
    border-radius: 6px;
    font-size: 1rem;
    cursor: pointer;
    color: white;
    font-weight: 600;
  }
  .download-btn { background-color: #8e24aa; }
  .dashboard-btn { background-color: #3949ab; }
  .dashboard-btn:hover { background-color: #303f9f; }
  @media print {
    #profile-toggle, .download-btn, .dashboard-btn { display: none; }
  }
  .footer { text-align: center; margin-top: 25px; color: #555; font-size: 0.95rem; }
</style>
</head>
<body>

<div class="summary-container" id="summary-report">
  <h1>MotherCare – Client Visit Summary Report</h1>
  <h2 id="client-name">Loading Client...</h2>

  <button id="profile-toggle">View Full Profile</button>
  <div id="profile-details"></div>
  <div id="profile-cards"></div>
  <canvas id="riskChart" width="800" height="350"></canvas>

  <button class="dashboard-btn" onclick="window.location.href='dashboard.php'">← Back to Dashboard</button>
  <button class="download-btn" onclick="window.print()">Download / Print Report</button>

  <div class="footer">Generated summary based on submitted visit entries.</div>
</div>

<script>
const apiUrl = 'VisitSummary.php'; // API already filters by logged-in user

fetch(apiUrl)
.then(res => res.json())
.then(data => {
  if (data.error) {
    document.querySelector(".summary-container").innerHTML = `<p style="color:red; text-align:center;">⚠ ${data.error}</p>`;
    return;
  }

  document.getElementById("client-name").textContent = data.name || "Client Summary";

  // Profile cards (basic)
  const profileFields = {
    "Nearest Health Facility": data.nearest_health,
    "Date of Birth": data.dob,
    "Location": `${data.district}, ${data.sub_county}, ${data.parish}, ${data.village}`,
    "Phone": data.kin_contact,
    "Email": data.email,
    "Registered On": data.registered_on
  };

  let cardsHTML = Object.entries(profileFields)
    .filter(([_, v]) => v && v !== 'N/A')
    .map(([k, v]) => `<div class="card low"><strong>${k}:</strong> ${v}</div>`)
    .join("");
  
  // Visits cards
  if (data.visits.length > 0) {
    data.visits.forEach(v => {
      let cls = "low";
      if (v.risk_level.toLowerCase() === "moderate") cls = "moderate";
      if (v.risk_level.toLowerCase() === "high") cls = "high";
      cardsHTML += `<div class="card ${cls}">
        <strong>Visit on ${v.date}:</strong> Risk Score = ${v.risk_score}, Level = ${v.risk_level}
      </div>`;
    });
  } else {
    cardsHTML += `<div class="card low">No visits recorded yet.</div>`;
  }

  document.getElementById("profile-cards").innerHTML = cardsHTML;

  // Full profile toggle
  const profileDetailsHTML = Object.entries(data)
    .filter(([key]) => key !== "visits")
    .map(([k, v]) => `<div><strong>${k.replace(/_/g, ' ')}:</strong> ${v}</div>`)
    .join("");
  document.getElementById("profile-details").innerHTML = profileDetailsHTML;

  // Chart
  const ctx = document.getElementById("riskChart").getContext("2d");
  const chartLabels = data.visits.length > 0 ? data.visits.map(v => v.date) : ["No data"];
  const chartData = data.visits.length > 0 ? data.visits.map(v => (v.risk_score !== 'N/A' ? parseFloat(v.risk_score) : 0)) : [0];

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartLabels,
      datasets: [{
        label: "Risk Score (%)",
        data: chartData,
        fill: true,
        borderColor: '#6a1b9a',
        backgroundColor: 'rgba(106, 27, 154, 0.2)',
        tension: 0.3,
        pointRadius: 5,
        pointHoverRadius: 7
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          title: { display: true, text: "Risk Level (%)" }
        },
        x: { title: { display: true, text: "Visit Date" } }
      },
      plugins: { legend: { display: true } }
    }
  });

})
.catch(() => {
  document.querySelector(".summary-container").innerHTML = `<p style="color:red; text-align:center;">⚠ Failed to fetch data. Please try again later.</p>`;
});

// Toggle profile view
document.getElementById("profile-toggle").addEventListener("click", () => {
  const details = document.getElementById("profile-details");
  if (details.style.display === "block") {
    details.style.display = "none";
    document.getElementById("profile-toggle").textContent = "View Full Profile";
  } else {
    details.style.display = "block";
    document.getElementById("profile-toggle").textContent = "Hide Profile";
  }
});
</script>

</body>
</html>