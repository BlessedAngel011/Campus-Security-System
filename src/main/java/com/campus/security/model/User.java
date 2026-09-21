package com.campus.security.model;

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

    // User's first name
    @Column(name = "first_name", nullable = false)
    private String firstName;

    // User's last name
    @Column(name = "last_name", nullable = false)
    private String lastName;

    // User's email address
    @Column(name = "email", nullable = false, unique = true)
    private String email;

    // User's phone number
    @Column(name = "phone_number")
    private String phoneNumber;

    // Password will be stored as a secure hash
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
    public User(Role role,
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

    // Getter and Setter for userId
    public Integer getUserId() {
        return userId;
    }

    public void setUserId(Integer userId) {
        this.userId = userId;
    }

    // Getter and Setter for role
    public Role getRole() {
        return role;
    }

    public void setRole(Role role) {
        this.role = role;
    }

    // Getter and Setter for campus
    public Campus getCampus() {
        return campus;
    }

    public void setCampus(Campus campus) {
        this.campus = campus;
    }

    // Getter and Setter for student/staff number
    public String getStudentStaffNumber() {
        return studentStaffNumber;
    }

    public void setStudentStaffNumber(String studentStaffNumber) {
        this.studentStaffNumber = studentStaffNumber;
    }

    // Getter and Setter for first name
    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    // Getter and Setter for last name
    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    // Getter and Setter for email
    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    // Getter and Setter for phone number
    public String getPhoneNumber() {
        return phoneNumber;
    }

    public void setPhoneNumber(String phoneNumber) {
        this.phoneNumber = phoneNumber;
    }

    // Getter and Setter for password hash
    public String getPasswordHash() {
        return passwordHash;
    }

    public void setPasswordHash(String passwordHash) {
        this.passwordHash = passwordHash;
    }

    // Getter and Setter for account status
    public AccountStatus getAccountStatus() {
        return accountStatus;
    }

    public void setAccountStatus(AccountStatus accountStatus) {
        this.accountStatus = accountStatus;
    }

    // Getter and Setter for emergency button
    public Boolean getEmergencyButtonEnabled() {
        return emergencyButtonEnabled;
    }

    public void setEmergencyButtonEnabled(Boolean emergencyButtonEnabled) {
        this.emergencyButtonEnabled = emergencyButtonEnabled;
    }

    // Getter and Setter for false alert count
    public Integer getFalseAlertCount() {
        return falseAlertCount;
    }

    public void setFalseAlertCount(Integer falseAlertCount) {
        this.falseAlertCount = falseAlertCount;
    }

    // Account status options
    public enum AccountStatus {
        ACTIVE,
        SUSPENDED,
        BLOCKED
    }
}