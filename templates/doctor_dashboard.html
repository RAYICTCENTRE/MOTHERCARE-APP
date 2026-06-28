<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Doctor Dashboard - MotherCare</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f0f4f8;
            display: flex;
            min-height: 100vh;
        }
        
        .sidebar {
            width: 260px;
            background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
            color: white;
            position: fixed;
            height: 100vh;
            padding: 20px 0;
        }
        
        .sidebar-header {
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .sidebar-header h2 { color: #fbbf24; font-size: 22px; }
        .sidebar-header p { font-size: 12px; opacity: 0.7; margin-top: 5px; }
        
        .sidebar-nav { padding: 20px 0; }
        
        .nav-item {
            padding: 12px 25px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: white;
            text-decoration: none;
            transition: all 0.3s;
            margin: 5px 15px;
            border-radius: 10px;
        }
        
        .nav-item:hover, .nav-item.active {
            background: rgba(255,255,255,0.15);
        }
        
        .nav-item i { width: 20px; }
        
        .main-content {
            flex: 1;
            margin-left: 260px;
            padding: 30px;
        }
        
        .top-bar {
            background: white;
            padding: 20px 30px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            border-left: 4px solid #1e3a8a;
        }
        
        .stat-card .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: #1e3a8a;
        }
        
        .section {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 30px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            text-align: left;
            padding: 12px;
            background: #f8f9fa;
            font-weight: 600;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }
        
        tr:hover { background: #f8f9fa; }
        
        .badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .badge-pending { background: #fff3cd; color: #856404; }
        .badge-active { background: #d4edda; color: #155724; }
        
        .btn {
            padding: 8px 15px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            background: #1e3a8a;
            color: white;
            text-decoration: none;
            font-size: 13px;
        }
        
        .btn:hover { opacity: 0.8; }
    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-header">
            <h2>MotherCare</h2>
            <p>Doctor Portal</p>
        </div>
        <div class="sidebar-nav">
            <a href="/doctor/dashboard" class="nav-item active">
                <i class="fas fa-tachometer-alt"></i> Dashboard
            </a>
            <a href="/doctor/patients" class="nav-item">
                <i class="fas fa-users"></i> My Patients
            </a>
            <a href="/doctor/consultations" class="nav-item">
                <i class="fas fa-stethoscope"></i> Consultations
            </a>
            <a href="/doctor/messages" class="nav-item">
                <i class="fas fa-envelope"></i> Messages
                {% if unread_messages > 0 %}
                    <span style="background: #dc3545; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-left: auto;">
                        {{ unread_messages }}
                    </span>
                {% endif %}
            </a>
            <a href="/doctor/profile" class="nav-item">
                <i class="fas fa-user-circle"></i> My Profile
            </a>
        </div>
    </div>

    <div class="main-content">
        <div class="top-bar">
            <h1>Welcome, Dr. {{ user.firstname }}</h1>
            <a href="/logout" class="btn" style="background: #dc3545;">
                <i class="fas fa-sign-out-alt"></i> Logout
            </a>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ total_patients }}</div>
                <div>Total Patients</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_consultations }}</div>
                <div>Consultations</div>
            </div>
            <div class="stat-card" style="border-left-color: #dc3545;">
                <div class="stat-number">{{ unread_messages }}</div>
                <div>Unread Messages</div>
            </div>
        </div>

        <div class="section">
            <h2><i class="fas fa-users"></i> My Patients</h2>
            <table>
                <thead>
                    <tr>
                        <th>Patient Name</th>
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Expected Delivery</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% if patients %}
                        {% for patient in patients %}
                        <tr>
                            <td><strong>{{ patient.firstname }} {{ patient.lastname }}</strong></td>
                            <td>{{ patient.email }}</td>
                            <td>{{ patient.phone if patient.phone else 'N/A' }}</td>
                            <td>{{ patient.expected_delivery if patient.expected_delivery else 'Not set' }}</td>
                            <td>
                                <a href="/doctor/view-patient/{{ patient.id }}" class="btn">View</a>
                                <a href="/chat-patient?patient_id={{ patient.id }}" class="btn" style="background: #28a745;">Chat</a>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="5" style="text-align: center; padding: 30px;">
                                No patients assigned yet.
                            </td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2><i class="fas fa-stethoscope"></i> Recent Consultations</h2>
            <table>
                <thead>
                    <tr>
                        <th>Patient</th>
                        <th>Date</th>
                        <th>Symptoms</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% if consultations %}
                        {% for consultation in consultations %}
                        <tr>
                            <td>{{ consultation.patient_name }}</td>
                            <td>{{ consultation.created_at.strftime('%Y-%m-%d') if consultation.created_at else 'N/A' }}</td>
                            <td>{{ consultation.symptoms[:50] if consultation.symptoms else 'N/A' }}...</td>
                            <td>
                                <span class="badge badge-{{ consultation.status }}">
                                    {{ consultation.status }}
                                </span>
                            </td>
                            <td>
                                <a href="/doctor/consultation/{{ consultation.id }}" class="btn">View</a>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="5" style="text-align: center; padding: 30px;">
                                No consultations yet.
                            </td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>

</body>
</html>
