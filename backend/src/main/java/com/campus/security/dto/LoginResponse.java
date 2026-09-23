package com.campus.security.dto;

import com.campus.security.model.User;
import java.time.LocalDateTime;

/**
 * Safe login response. The session token is intentionally returned
 * only here; UserSession itself hides it from JSON serialization.
 */
public class LoginResponse {

    private Integer sessionId;
    private String sessionToken;
    private Integer userId;
    private String role;
    private Integer campusId;
    private String studentStaffNumber;
    private String firstName;
    private String lastName;
    private String email;
    private LocalDateTime expiryTime;

    public LoginResponse() {
    }

    public LoginResponse(
            Integer sessionId,
            String sessionToken,
            User user,
            LocalDateTime expiryTime) {

        this.sessionId = sessionId;
        this.sessionToken = sessionToken;
        this.userId = user.getUserId();
        this.role = user.getRole().getRoleName();
        this.campusId = user.getCampus().getCampusId();
        this.studentStaffNumber = user.getStudentStaffNumber();
        this.firstName = user.getFirstName();
        this.lastName = user.getLastName();
        this.email = user.getEmail();
        this.expiryTime = expiryTime;
    }

    public Integer getSessionId() { return sessionId; }
    public String getSessionToken() { return sessionToken; }
    public Integer getUserId() { return userId; }
    public String getRole() { return role; }
    public Integer getCampusId() { return campusId; }
    public String getStudentStaffNumber() { return studentStaffNumber; }
    public String getFirstName() { return firstName; }
    public String getLastName() { return lastName; }
    public String getEmail() { return email; }
    public LocalDateTime getExpiryTime() { return expiryTime; }
}
