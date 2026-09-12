package com.campus.security.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "false_alerts")
public class FalseAlert {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "false_alert_id")
    private Integer falseAlertId;

    @ManyToOne
    @JoinColumn(name = "emergency_id", nullable = false)
    private EmergencyAlert emergencyAlert;

    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne
    @JoinColumn(name = "reviewed_by_admin")
    private Administrator reviewedByAdmin;

    @Column(name = "reason")
    private String reason;

    @Enumerated(EnumType.STRING)
    @Column(name = "false_alert_status")
    private FalseAlertStatus falseAlertStatus = FalseAlertStatus.PENDING;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "reviewed_at")
    private LocalDateTime reviewedAt;

    public FalseAlert() {
    }

    public Integer getFalseAlertId() {
        return falseAlertId;
    }

    public void setFalseAlertId(Integer falseAlertId) {
        this.falseAlertId = falseAlertId;
    }

    public EmergencyAlert getEmergencyAlert() {
        return emergencyAlert;
    }

    public void setEmergencyAlert(EmergencyAlert emergencyAlert) {
        this.emergencyAlert = emergencyAlert;
    }

    public User getUser() {
        return user;
    }

    public void setUser(User user) {
        this.user = user;
    }

    public Administrator getReviewedByAdmin() {
        return reviewedByAdmin;
    }

    public void setReviewedByAdmin(Administrator reviewedByAdmin) {
        this.reviewedByAdmin = reviewedByAdmin;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }

    public FalseAlertStatus getFalseAlertStatus() {
        return falseAlertStatus;
    }

    public void setFalseAlertStatus(FalseAlertStatus falseAlertStatus) {
        this.falseAlertStatus = falseAlertStatus;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getReviewedAt() {
        return reviewedAt;
    }

    public void setReviewedAt(LocalDateTime reviewedAt) {
        this.reviewedAt = reviewedAt;
    }

    public enum FalseAlertStatus {
        PENDING,
        CONFIRMED_FALSE,
        NOT_FALSE
    }
}