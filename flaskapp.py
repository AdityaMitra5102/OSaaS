from flask import Flask, request, render_template_string, jsonify, send_file
import sqlite3
import hashlib
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'osfiles'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

HOSTNAME = '192.168.1.53:5000'
DB_FILE = 'enterprise_os.db'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # OS Files table
    c.execute('''CREATE TABLE IF NOT EXISTS os_files
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  original_filename TEXT NOT NULL,
                  stored_filename TEXT NOT NULL UNIQUE,
                  md5_hash TEXT NOT NULL,
                  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # OS Definitions table
    c.execute('''CREATE TABLE IF NOT EXISTS os_definitions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  os_name TEXT NOT NULL UNIQUE,
                  definition TEXT NOT NULL,
                  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL UNIQUE,
                  password_hash TEXT NOT NULL,
                  assigned_os TEXT,
                  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Logs table
    c.execute('''CREATE TABLE IF NOT EXISTS auth_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL,
                  mac_address TEXT,
                  success INTEGER NOT NULL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise OS Server</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
            transition: background 0.3s, color 0.3s;
        }
        
        body.dark-mode {
            background: #1a1a1a;
            color: #e0e0e0;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: relative;
        }
        
        .dark-mode-toggle {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .dark-mode-toggle:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 600;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #ddd;
        }
        
        .tab {
            padding: 12px 24px;
            background: white;
            border: none;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            color: #666;
            border-radius: 8px 8px 0 0;
            transition: all 0.3s;
        }
        
        .tab:hover {
            background: #f0f0f0;
        }
        
        .tab.active {
            background: #667eea;
            color: white;
        }
        
        .subtabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .subtab {
            padding: 10px 20px;
            background: white;
            border: 2px solid #ddd;
            cursor: pointer;
            font-size: 14px;
            border-radius: 6px;
            transition: all 0.3s;
            color: #333;
        }
        
        .dark-mode .subtab {
            background: #3a3a3a;
            border-color: #4a4a4a;
            color: #e0e0e0;
        }
        
        .subtab:hover {
            border-color: #667eea;
        }
        
        .subtab.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .tab-content {
            display: none;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: background 0.3s, box-shadow 0.3s;
        }
        
        .dark-mode .tab-content {
            background: #2a2a2a;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        .tab-content.active {
            display: block;
        }
        
        .subtab-content {
            display: none;
        }
        
        .subtab-content.active {
            display: block;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #555;
        }
        
        .dark-mode label {
            color: #b0b0b0;
        }
        
        input[type="text"],
        input[type="password"],
        input[type="file"],
        select,
        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s, background 0.3s, color 0.3s;
            background: white;
            color: #333;
        }
        
        .dark-mode input[type="text"],
        .dark-mode input[type="password"],
        .dark-mode input[type="file"],
        .dark-mode select,
        .dark-mode textarea {
            background: #3a3a3a;
            border-color: #4a4a4a;
            color: #e0e0e0;
        }
        
        input:focus,
        select:focus,
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        textarea {
            font-family: 'Courier New', monospace;
            min-height: 300px;
            resize: vertical;
        }
        
        button {
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #5568d3;
        }
        
        button.danger {
            background: #e74c3c;
        }
        
        button.danger:hover {
            background: #c0392b;
        }
        
        .file-list,
        .os-list,
        .user-list,
        .log-list {
            margin-top: 30px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        th,
        td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }
        
        .dark-mode th {
            background: #3a3a3a;
            color: #b0b0b0;
        }
        
        .dark-mode td {
            border-bottom-color: #3a3a3a;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .dark-mode tr:hover {
            background: #333;
        }
        
        .drop-zone {
            display: none;
        }
        
        .success {
            color: #27ae60;
            font-weight: 500;
        }
        
        .error {
            color: #e74c3c;
            font-weight: 500;
        }
        
        .message {
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .action-buttons {
            display: flex;
            gap: 10px;
        }
        
        .os-select-container {
            margin-bottom: 20px;
        }
        
        .hostname-info {
            background: #e8f4f8;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-family: monospace;
            color: #0366d6;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>🖥️ Enterprise OS Server</h1>
            <button class="dark-mode-toggle" onclick="toggleDarkMode()">🌙 Dark Mode</button>
        </div>
    </div>
    
    <div class="container">
        <div class="hostname-info">
            Current Hostname: <strong>{{ hostname }}</strong>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('os')">OS Management</button>
            <button class="tab" onclick="switchTab('users')">User Management</button>
            <button class="tab" onclick="switchTab('logs')">Authentication Logs</button>
        </div>
        
        <!-- OS Tab -->
        <div id="os-tab" class="tab-content active">
            <div class="subtabs">
                <button class="subtab active" onclick="switchSubtab('os-files')">OS Files</button>
                <button class="subtab" onclick="switchSubtab('os-definitions')">OS Definitions</button>
            </div>
            
            <!-- OS Files Subtab -->
            <div id="os-files-subtab" class="subtab-content active">
                <h2>Upload OS Files</h2>
                <div class="form-group">
                    <label for="file-upload">Select File to Upload</label>
                    <input type="file" id="file-upload">
                    <button onclick="uploadFile()" style="margin-top: 10px;">Upload File</button>
                </div>
                
                <div id="upload-message"></div>
                
                <div class="file-list">
                    <h3>Uploaded Files</h3>
                    <table id="files-table">
                        <thead>
                            <tr>
                                <th>Original Filename</th>
                                <th>Stored Filename</th>
                                <th>MD5 Hash</th>
                                <th>Upload Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="files-tbody"></tbody>
                    </table>
                </div>
            </div>
            
            <!-- OS Definitions Subtab -->
            <div id="os-definitions-subtab" class="subtab-content">
                <h2>OS Definitions</h2>
                
                <div class="os-select-container">
                    <label>Select OS to Edit:</label>
                    <select id="os-select" onchange="loadOSDefinition()">
                        <option value="">-- Create New OS --</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="os-name">OS Name</label>
                    <input type="text" id="os-name" placeholder="e.g., CustomOS1">
                </div>
                
                <div class="form-group">
                    <label for="os-definition">OS Definition (iPXE Script) - Drag files from the table below to insert URLs</label>
                    <textarea id="os-definition" placeholder="#!ipxe&#10;dhcp&#10;kernel http://...&#10;initrd http://...&#10;boot"></textarea>
                </div>
                
                <div id="os-message"></div>
                
                <div class="action-buttons">
                    <button onclick="saveOSDefinition()">Save OS Definition</button>
                    <button class="danger" onclick="deleteOSDefinition()">Delete OS</button>
                </div>
                
                <div class="file-list">
                    <h3>Available Files (Drag to textarea above)</h3>
                    <table id="files-table-def">
                        <thead>
                            <tr>
                                <th>Original Filename</th>
                                <th>Stored Filename</th>
                                <th>MD5 Hash</th>
                            </tr>
                        </thead>
                        <tbody id="files-tbody-def"></tbody>
                    </table>
                </div>
                
                <div class="os-list" style="margin-top: 40px;">
                    <h3>Available OS Definitions</h3>
                    <table id="os-table">
                        <thead>
                            <tr>
                                <th>OS Name</th>
                                <th>Created Date</th>
                                <th>Modified Date</th>
                            </tr>
                        </thead>
                        <tbody id="os-tbody"></tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Users Tab -->
        <div id="users-tab" class="tab-content">
            <h2>User Management</h2>
            
            <div class="form-group">
                <label for="user-username">Username</label>
                <input type="text" id="user-username" placeholder="Enter username">
            </div>
            
            <div class="form-group">
                <label for="user-password">Password</label>
                <input type="password" id="user-password" placeholder="Enter password">
            </div>
            
            <div class="form-group">
                <label for="user-os">Assigned OS</label>
                <select id="user-os">
                    <option value="">-- No OS Assigned --</option>
                </select>
            </div>
            
            <div id="user-message"></div>
            
            <div class="action-buttons">
                <button onclick="saveUser()">Save User</button>
                <button onclick="clearUserForm()">Clear Form</button>
            </div>
            
            <div class="user-list">
                <h3>Existing Users</h3>
                <table id="users-table">
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Assigned OS</th>
                            <th>Created Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="users-tbody"></tbody>
                </table>
            </div>
        </div>
        
        <!-- Logs Tab -->
        <div id="logs-tab" class="tab-content">
            <h2>Authentication Logs</h2>
            
            <button onclick="loadLogs()" style="margin-bottom: 20px;">Refresh Logs</button>
            
            <div class="log-list">
                <table id="logs-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Username</th>
                            <th>MAC Address</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="logs-tbody"></tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        const hostname = "{{ hostname }}";
        
        // Dark mode toggle
        function toggleDarkMode() {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDark);
            
            const toggleBtn = document.querySelector('.dark-mode-toggle');
            toggleBtn.textContent = isDark ? '☀️ Light Mode' : '🌙 Dark Mode';
        }
        
        // Load dark mode preference
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark-mode');
            document.querySelector('.dark-mode-toggle').textContent = '☀️ Light Mode';
        }
        
        // Tab switching
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName + '-tab').classList.add('active');
            
            if (tabName === 'os') {
                loadFiles();
                loadOSList();
            } else if (tabName === 'users') {
                loadUsers();
                loadOSListForUsers();
            } else if (tabName === 'logs') {
                loadLogs();
            }
        }
        
        function switchSubtab(subtabName) {
            document.querySelectorAll('.subtab').forEach(st => st.classList.remove('active'));
            document.querySelectorAll('.subtab-content').forEach(stc => stc.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(subtabName + '-subtab').classList.add('active');
            
            if (subtabName === 'os-files') {
                loadFiles();
            } else if (subtabName === 'os-definitions') {
                loadOSList();
                loadFiles(); // Load files for dragging
            }
        }
        
        // File upload
        async function uploadFile() {
            const fileInput = document.getElementById('file-upload');
            const file = fileInput.files[0];
            
            if (!file) {
                showMessage('upload-message', 'Please select a file', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('upload-message', 'File uploaded successfully', 'success');
                    fileInput.value = '';
                    loadFiles();
                } else {
                    showMessage('upload-message', 'Error: ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('upload-message', 'Upload failed: ' + error, 'error');
            }
        }
        
        async function loadFiles() {
            try {
                const response = await fetch('/api/files');
                const data = await response.json();
                
                const tbody = document.getElementById('files-tbody');
                const tbodyDef = document.getElementById('files-tbody-def');
                tbody.innerHTML = '';
                if (tbodyDef) tbodyDef.innerHTML = '';
                
                data.files.forEach(file => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${file.original_filename}</td>
                        <td>${file.stored_filename}</td>
                        <td style="font-family: monospace; font-size: 12px;">${file.md5_hash}</td>
                        <td>${new Date(file.upload_date).toLocaleString()}</td>
                        <td>
                            <button onclick="deleteFile('${file.stored_filename}')" class="danger" style="padding: 6px 12px;">Delete</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                    
                    // Also add to OS definitions tab
                    if (tbodyDef) {
                        const trDef = document.createElement('tr');
                        trDef.innerHTML = `
                            <td>${file.original_filename}</td>
                            <td>${file.stored_filename}</td>
                            <td style="font-family: monospace; font-size: 12px;">${file.md5_hash}</td>
                        `;
                        tbodyDef.appendChild(trDef);
                    }
                });
            } catch (error) {
                console.error('Failed to load files:', error);
            }
        }
        
        async function deleteFile(filename) {
            if (!confirm('Are you sure you want to delete this file?')) {
                return;
            }
            
            try {
                const response = await fetch('/api/file/' + filename, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('upload-message', 'File deleted successfully', 'success');
                    loadFiles();
                } else {
                    showMessage('upload-message', 'Error: ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('upload-message', 'Delete failed: ' + error, 'error');
            }
        }
        
        // Drag and drop for OS definition - drop on textarea
        const textarea = document.getElementById('os-definition');
        
        textarea.addEventListener('dragover', (e) => {
            e.preventDefault();
            textarea.style.borderColor = '#667eea';
            textarea.style.background = '#f0f4ff';
        });
        
        textarea.addEventListener('dragleave', () => {
            textarea.style.borderColor = '#ddd';
            textarea.style.background = 'white';
        });
        
        textarea.addEventListener('drop', (e) => {
            e.preventDefault();
            textarea.style.borderColor = '#ddd';
            textarea.style.background = 'white';
            
            const filename = e.dataTransfer.getData('text/plain');
            if (filename) {
                const url = `http://${hostname}/osfiles/${filename}`;
                const currentText = textarea.value;
                const cursorPos = textarea.selectionStart;
                
                textarea.value = currentText.slice(0, cursorPos) + url + currentText.slice(cursorPos);
                textarea.focus();
                textarea.selectionStart = textarea.selectionEnd = cursorPos + url.length;
            }
        });
        
        // Make file rows draggable
        document.addEventListener('DOMContentLoaded', () => {
            loadFiles();
            loadOSList();
        });
        
        // Attach drag event to file rows
        function makeDraggable() {
            const rows = document.querySelectorAll('#files-tbody tr, #files-tbody-def tr');
            rows.forEach(row => {
                row.draggable = true;
                row.style.cursor = 'move';
                row.addEventListener('dragstart', (e) => {
                    const filename = row.cells[1].textContent;
                    e.dataTransfer.setData('text/plain', filename);
                    e.dataTransfer.effectAllowed = 'copy';
                });
            });
        }
        
        // Override loadFiles to make rows draggable
        const originalLoadFiles = loadFiles;
        loadFiles = async function() {
            await originalLoadFiles();
            makeDraggable();
        };
        
        // OS Definition management
        async function loadOSList() {
            try {
                const response = await fetch('/api/os-definitions');
                const data = await response.json();
                
                const select = document.getElementById('os-select');
                const tbody = document.getElementById('os-tbody');
                
                select.innerHTML = '<option value="">-- Create New OS --</option>';
                tbody.innerHTML = '';
                
                data.os_list.forEach(os => {
                    const option = document.createElement('option');
                    option.value = os.os_name;
                    option.textContent = os.os_name;
                    select.appendChild(option);
                    
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${os.os_name}</td>
                        <td>${new Date(os.created_date).toLocaleString()}</td>
                        <td>${new Date(os.modified_date).toLocaleString()}</td>
                    `;
                    tr.style.cursor = 'pointer';
                    tr.onclick = () => {
                        select.value = os.os_name;
                        loadOSDefinition();
                    };
                    tbody.appendChild(tr);
                });
            } catch (error) {
                console.error('Failed to load OS list:', error);
            }
        }
        
        async function loadOSDefinition() {
            const osName = document.getElementById('os-select').value;
            
            if (!osName) {
                document.getElementById('os-name').value = '';
                document.getElementById('os-definition').value = '';
                return;
            }
            
            try {
                const response = await fetch('/api/os-definition/' + osName);
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('os-name').value = data.os.os_name;
                    document.getElementById('os-definition').value = data.os.definition;
                }
            } catch (error) {
                console.error('Failed to load OS definition:', error);
            }
        }
        
        async function saveOSDefinition() {
            const osName = document.getElementById('os-name').value.trim();
            const definition = document.getElementById('os-definition').value;
            
            if (!osName) {
                showMessage('os-message', 'Please enter an OS name', 'error');
                return;
            }
            
            if (!definition) {
                showMessage('os-message', 'Please enter an OS definition', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/os-definition', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ os_name: osName, definition: definition })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('os-message', 'OS definition saved successfully', 'success');
                    loadOSList();
                    document.getElementById('os-select').value = osName;
                } else {
                    showMessage('os-message', 'Error: ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('os-message', 'Save failed: ' + error, 'error');
            }
        }
        
        async function deleteOSDefinition() {
            const osName = document.getElementById('os-name').value.trim();
            
            if (!osName) {
                showMessage('os-message', 'Please select an OS to delete', 'error');
                return;
            }
            
            if (!confirm(`Are you sure you want to delete OS "${osName}"?`)) {
                return;
            }
            
            try {
                const response = await fetch('/api/os-definition/' + osName, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('os-message', 'OS definition deleted successfully', 'success');
                    document.getElementById('os-name').value = '';
                    document.getElementById('os-definition').value = '';
                    document.getElementById('os-select').value = '';
                    loadOSList();
                } else {
                    showMessage('os-message', 'Error: ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('os-message', 'Delete failed: ' + error, 'error');
            }
        }
        
        // User management
        let editingUser = null;
        
        async function loadOSListForUsers() {
            try {
                const response = await fetch('/api/os-definitions');
                const data = await response.json();
                
                const select = document.getElementById('user-os');
                select.innerHTML = '<option value="">-- No OS Assigned --</option>';
                
                data.os_list.forEach(os => {
                    const option = document.createElement('option');
                    option.value = os.os_name;
                    option.textContent = os.os_name;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Failed to load OS list:', error);
            }
        }
        
        function clearUserForm() {
            document.getElementById('user-username').value = '';
            document.getElementById('user-password').value = '';
            document.getElementById('user-os').value = '';
            document.getElementById('user-username').disabled = false;
            editingUser = null;
        }
        
        function editUser(username, assignedOS) {
            editingUser = username;
            document.getElementById('user-username').value = username;
            document.getElementById('user-username').disabled = true;
            document.getElementById('user-password').value = '';
            document.getElementById('user-password').placeholder = 'Leave blank to keep current password';
            document.getElementById('user-os').value = assignedOS || '';
            window.scrollTo(0, 0);
        }
        
        async function saveUser() {
            const username = document.getElementById('user-username').value.trim();
            const password = document.getElementById('user-password').value;
            const assignedOS = document.getElementById('user-os').value;
            
            if (!username) {
                showMessage('user-message', 'Please enter a username', 'error');
                return;
            }
            
            if (!editingUser && !password) {
                showMessage('user-message', 'Please enter a password for new user', 'error');
                return;
            }
            
            try {
                let response;
                if (editingUser) {
                    // Update existing user
                    response = await fetch('/api/user/' + username, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            password: password || null,
                            assigned_os: assignedOS
                        })
                    });
                } else {
                    // Create new user
                    response = await fetch('/api/user', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            username: username,
                            password: password,
                            assigned_os: assignedOS
                        })
                    });
                }
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('user-message', editingUser ? 'User updated successfully' : 'User created successfully', 'success');
                    clearUserForm();
                    loadUsers();
                } else {
                    showMessage('user-message', 'Error: ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('user-message', 'Failed to save user: ' + error, 'error');
            }
        }
        
        async function loadUsers() {
            try {
                const response = await fetch('/api/users');
                const data = await response.json();
                
                const tbody = document.getElementById('users-tbody');
                tbody.innerHTML = '';
                
                data.users.forEach(user => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${user.username}</td>
                        <td>${user.assigned_os || 'None'}</td>
                        <td>${new Date(user.created_date).toLocaleString()}</td>
                        <td>
                            <button onclick="editUser('${user.username}', '${user.assigned_os || ''}')" style="padding: 6px 12px; margin-right: 5px;">Edit</button>
                            <button onclick="deleteUser('${user.username}')" class="danger" style="padding: 6px 12px;">Delete</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (error) {
                console.error('Failed to load users:', error);
            }
        }
        
        async function deleteUser(username) {
            if (!confirm(`Are you sure you want to delete user "${username}"?`)) {
                return;
            }
            
            try {
                const response = await fetch('/api/user/' + username, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('user-message', 'User deleted successfully', 'success');
                    loadUsers();
                } else {
                    showMessage('user-message', 'Error: ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('user-message', 'Delete failed: ' + error, 'error');
            }
        }
        
        // Logs
        async function loadLogs() {
            try {
                const response = await fetch('/api/logs');
                const data = await response.json();
                
                const tbody = document.getElementById('logs-tbody');
                tbody.innerHTML = '';
                
                data.logs.forEach(log => {
                    const tr = document.createElement('tr');
                    const status = log.success ? '<span class="success">✓ Success</span>' : '<span class="error">✗ Failed</span>';
                    tr.innerHTML = `
                        <td>${new Date(log.timestamp).toLocaleString()}</td>
                        <td>${log.username}</td>
                        <td style="font-family: monospace;">${log.mac_address || 'N/A'}</td>
                        <td>${status}</td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (error) {
                console.error('Failed to load logs:', error);
            }
        }
        
        // Helper function
        function showMessage(elementId, message, type) {
            const element = document.getElementById(elementId);
            element.innerHTML = `<div class="message ${type}">${message}</div>`;
            setTimeout(() => {
                element.innerHTML = '';
            }, 5000);
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, hostname=HOSTNAME)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    try:
        # Read file content
        file_content = file.read()
        
        # Calculate MD5 hash
        md5_hash = hashlib.md5(file_content).hexdigest()
        
        # Get original filename and extension
        original_filename = secure_filename(file.filename)
        
        # Split filename and extension
        if '.' in original_filename:
            name_parts = original_filename.rsplit('.', 1)
            base_name = name_parts[0]
            extension = '.' + name_parts[1]
        else:
            base_name = original_filename
            extension = ''
        
        # Create stored filename with MD5
        stored_filename = f"{base_name}-{md5_hash}{extension}"
        
        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Save to database
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''INSERT INTO os_files (original_filename, stored_filename, md5_hash)
                     VALUES (?, ?, ?)''', (original_filename, stored_filename, md5_hash))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'File uploaded successfully',
                       'stored_filename': stored_filename})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/files', methods=['GET'])
def get_files():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT original_filename, stored_filename, md5_hash, upload_date FROM os_files ORDER BY upload_date DESC')
    files = []
    for row in c.fetchall():
        files.append({
            'original_filename': row[0],
            'stored_filename': row[1],
            'md5_hash': row[2],
            'upload_date': row[3]
        })
    conn.close()
    return jsonify({'files': files})

@app.route('/api/file/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        # Delete from filesystem
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('DELETE FROM os_files WHERE stored_filename = ?', (filename,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/osfiles/<filename>')
def serve_os_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return send_file(file_path)
    except Exception as e:
        return f"File not found: {e}", 404

@app.route('/api/os-definitions', methods=['GET'])
def get_os_definitions():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT os_name, created_date, modified_date FROM os_definitions ORDER BY os_name')
    os_list = []
    for row in c.fetchall():
        os_list.append({
            'os_name': row[0],
            'created_date': row[1],
            'modified_date': row[2]
        })
    conn.close()
    return jsonify({'os_list': os_list})

@app.route('/api/os-definition/<os_name>', methods=['GET'])
def get_os_definition(os_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT os_name, definition FROM os_definitions WHERE os_name = ?', (os_name,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            'success': True,
            'os': {
                'os_name': row[0],
                'definition': row[1]
            }
        })
    else:
        return jsonify({'success': False, 'message': 'OS not found'})

@app.route('/api/os-definition', methods=['POST'])
def save_os_definition():
    data = request.json
    os_name = data.get('os_name', '').strip()
    definition = data.get('definition', '')
    
    if not os_name:
        return jsonify({'success': False, 'message': 'OS name is required'})
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Check if OS exists
        c.execute('SELECT id FROM os_definitions WHERE os_name = ?', (os_name,))
        exists = c.fetchone()
        
        if exists:
            # Update existing
            c.execute('''UPDATE os_definitions 
                        SET definition = ?, modified_date = CURRENT_TIMESTAMP 
                        WHERE os_name = ?''', (definition, os_name))
        else:
            # Insert new
            c.execute('''INSERT INTO os_definitions (os_name, definition)
                        VALUES (?, ?)''', (os_name, definition))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/os-definition/<os_name>', methods=['DELETE'])
def delete_os_definition(os_name):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('DELETE FROM os_definitions WHERE os_name = ?', (os_name,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/user', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    assigned_os = data.get('assigned_os', '')
    
    if not username:
        return jsonify({'success': False, 'message': 'Username is required'})
    
    if not password:
        return jsonify({'success': False, 'message': 'Password is required'})
    
    # Hash password with SHA256
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''INSERT INTO users (username, password_hash, assigned_os)
                     VALUES (?, ?, ?)''', (username, password_hash, assigned_os if assigned_os else None))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Username already exists'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT username, assigned_os, created_date FROM users ORDER BY created_date DESC')
    users = []
    for row in c.fetchall():
        users.append({
            'username': row[0],
            'assigned_os': row[1],
            'created_date': row[2]
        })
    conn.close()
    return jsonify({'users': users})

@app.route('/api/user/<username>', methods=['DELETE'])
def delete_user(username):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('DELETE FROM users WHERE username = ?', (username,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/user/<username>', methods=['PUT'])
def update_user(username):
    data = request.json
    password = data.get('password')
    assigned_os = data.get('assigned_os', '')
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # If password is provided, update it
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            c.execute('''UPDATE users 
                        SET password_hash = ?, assigned_os = ?
                        WHERE username = ?''', (password_hash, assigned_os if assigned_os else None, username))
        else:
            # Only update assigned OS
            c.execute('''UPDATE users 
                        SET assigned_os = ?
                        WHERE username = ?''', (assigned_os if assigned_os else None, username))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT username, mac_address, success, timestamp FROM auth_logs ORDER BY timestamp DESC LIMIT 100')
    logs = []
    for row in c.fetchall():
        logs.append({
            'username': row[0],
            'mac_address': row[1],
            'success': row[2],
            'timestamp': row[3]
        })
    conn.close()
    return jsonify({'logs': logs})

@app.route('/init')
def init_route():
    script = f"""#!ipxe
login
chain http://{HOSTNAME}/getos?username=${{username}}&password=${{password}}&mac=${{mac}}"""
    return script, 200, {'Content-Type': 'text/plain'}

@app.route('/getos')
def get_os():
    username = request.args.get('username', '')
    password = request.args.get('password', '')
    mac = request.args.get('mac', '')
    
    # Hash the provided password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Check credentials
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT assigned_os FROM users 
                 WHERE username = ? AND password_hash = ?''', (username, password_hash))
    result = c.fetchone()
    
    if result and result[0]:
        assigned_os = result[0]
        
        # Get OS definition
        c.execute('SELECT definition FROM os_definitions WHERE os_name = ?', (assigned_os,))
        os_def = c.fetchone()
        
        if os_def:
            # Log successful authentication
            c.execute('''INSERT INTO auth_logs (username, mac_address, success)
                        VALUES (?, ?, 1)''', (username, mac))
            conn.commit()
            conn.close()
            
            return os_def[0], 200, {'Content-Type': 'text/plain'}
    
    # Log failed authentication
    c.execute('''INSERT INTO auth_logs (username, mac_address, success)
                VALUES (?, ?, 0)''', (username, mac))
    conn.commit()
    conn.close()
    
    # Return error script
    error_script = f"""#!ipxe
prompt Invalid credentials
chain http://{HOSTNAME}/init"""
    return error_script, 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
