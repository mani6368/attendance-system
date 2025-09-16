function updateAttendance() {
    Promise.all([
        fetch('/api/attendance/today').then(res => res.json()),
        fetch('/api/people').then(res => res.json())
    ])
    .then(([attendance, people]) => {
        // Update attendance table
        updateAttendanceTable(attendance);
        // Update people list
        updatePeopleList(people);

            // Update attendance table
            const tableBody = document.getElementById('attendance-table-body');
            tableBody.innerHTML = '';
            data.attendance.forEach(entry => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${entry.person}</td>
                    <td>${entry.date}</td>
                    <td>${entry.time}</td>
                    <td>${entry.status}</td>
                `;
                tableBody.appendChild(row);
            });

            // Update face images
            const faceImages = document.getElementById('face-images');
            faceImages.innerHTML = '';
            data.face_images.forEach(image => {
                const img = document.createElement('img');
                img.src = `/detected_faces/${image}`;
                img.className = 'face-image';
                faceImages.appendChild(img);
            });
        })
        .catch(error => console.error('Error:', error));
}

// Update every 5 seconds
setInterval(updateAttendance, 5000);

// Initial update
document.addEventListener('DOMContentLoaded', updateAttendance);