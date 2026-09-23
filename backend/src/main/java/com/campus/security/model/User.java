package com.campus.security.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;

@Entity
@Table(name = "users")
public class User {

    // Primary key
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "user_id")
    private Integer userId;

    // Relationship with the roles table
    @ManyToOne
    @JoinColumn(name = "role_id", nullable = false)
    private Role role;

    // Relationship with the campuses table
    @ManyToOne
    @JoinColumn(name = "campus_id", nullable = false)
    private Campus campus;

    // Student or staff number
    @Column(name = "student_staff_number", nullable = false, unique = true)
    private String studentStaffNumber;

    // First name
    @Column(name = "first_name", nullable = false)
    private String firstName;

    // Last name
    @Column(name = "last_name", nullable = false)
    private String lastName;

    // Email address
    @Column(name = "email", nullable = false, unique = true)
    private String email;

    // Phone number
    @Column(name = "phone_number")
    private String phoneNumber;

    // Password stored as a secure hash
    @JsonIgnore
    @Column(name = "password_hash", nullable = false)
    private String passwordHash;

    // Account status
    @Enumerated(EnumType.STRING)
    @Column(name = "account_status")
    private AccountStatus accountStatus = AccountStatus.ACTIVE;

    // Determines whether the emergency button can be used
    @Column(name = "emergency_button_enabled")
    private Boolean emergencyButtonEnabled = true;

    // Number of confirmed false emergency alerts
    @Column(name = "false_alert_count")
    private Integer falseAlertCount = 0;


    // Empty constructor required by JPA
    public User() {
    }


    // Constructor
    public User(
            Role role,
            Campus campus,
            String studentStaffNumber,
            String firstName,
            String lastName,
            String email,
            String phoneNumber,
            String passwordHash) {

        this.role = role;
        this.campus = campus;
        this.studentStaffNumber = studentStaffNumber;
        this.firstName = firstName;
        this.lastName = lastName;
        this.email = email;
        this.phoneNumber = phoneNumber;
        this.passwordHash = passwordHash;
    }


    // =========================
    // USER ID
    // =========================

    public Integer getUserId() {
        return userId;
    }

    public void setUserId(Integer userId) {
        this.userId = userId;
    }


    // =========================
    // ROLE
    // =========================

    public Role getRole() {
        return role;
    }

    public void setRole(Role role) {
        this.role = role;
    }


    // =========================
    // CAMPUS
    // =========================

    public Campus getCampus() {
        return campus;
    }

    public void setCampus(Campus campus) {
        this.campus = campus;
    }


    // =========================
    // STUDENT / STAFF NUMBER
    // =========================

    public String getStudentStaffNumber() {
        return studentStaffNumber;
    }

    public void setStudentStaffNumber(String studentStaffNumber) {
        this.studentStaffNumber = studentStaffNumber;
    }


    // =========================
    // FIRST NAME
    // =========================

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }


    // =========================
    // LAST NAME
    // =========================

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }


    // =========================
    // EMAIL
    // =========================

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }


    // =========================
    // PHONE NUMBER
    // =========================

    public String getPhoneNumber() {
        return phoneNumber;
    }

    public void setPhoneNumber(String phoneNumber) {
        this.phoneNumber = phoneNumber;
    }


    // =========================
    // PASSWORD HASH
    // =========================

    public String getPasswordHash() {
        return passwordHash;
    }

    public void setPasswordHash(String passwordHash) {
        this.passwordHash = passwordHash;
    }


    // =========================
    // ACCOUNT STATUS
    // =========================

    public AccountStatus getAccountStatus() {
        return accountStatus;
    }

    public void setAccountStatus(AccountStatus accountStatus) {
        this.accountStatus = accountStatus;
    }


    // =========================
    // EMERGENCY BUTTON
    // =========================

    public Boolean getEmergencyButtonEnabled() {
        return emergencyButtonEnabled;
    }

    public void setEmergencyButtonEnabled(Boolean emergencyButtonEnabled) {
        this.emergencyButtonEnabled = emergencyButtonEnabled;
    }


    // =========================
    // FALSE ALERT COUNT
    // =========================

    public Integer getFalseAlertCount() {
        return falseAlertCount;
    }

    public void setFalseAlertCount(Integer falseAlertCount) {
        this.falseAlertCount = falseAlertCount;
    }


    // =========================
    // ACCOUNT STATUS ENUM
    // =========================

    public enum AccountStatus {
        ACTIVE,
        SUSPENDED,
        BLOCKED
    }
}

