package com.campus.security.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "alert_assignments")
public class AlertAssignment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "assignment_id")
    private Integer assignmentId;

    @ManyToOne
    @JoinColumn(name = "emergency_id", nullable = false)
    private EmergencyAlert emergencyAlert;

    @ManyToOne
    @JoinColumn(name = "officer_id", nullable = false)
    private SecurityOfficer officer;

    @Column(name = "distance_km")
    private Double distanceKm;

    @Enumerated(EnumType.STRING)
    @Column(name = "assignment_status")
    private AssignmentStatus assignmentStatus = AssignmentStatus.ASSIGNED;

    @Column(name = "assigned_at")
    private LocalDateTime assignedAt;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    public AlertAssignment() {
    }

    public Integer getAssignmentId() {
        return assignmentId;
    }

    public void setAssignmentId(Integer assignmentId) {
        this.assignmentId = assignmentId;
    }

    public EmergencyAlert getEmergencyAlert() {
        return emergencyAlert;
    }

    public void setEmergencyAlert(EmergencyAlert emergencyAlert) {
        this.emergencyAlert = emergencyAlert;
    }

    public SecurityOfficer getOfficer() {
        return officer;
    }

    public void setOfficer(SecurityOfficer officer) {
        this.officer = officer;
    }

    public Double getDistanceKm() {
        return distanceKm;
    }

    public void setDistanceKm(Double distanceKm) {
        this.distanceKm = distanceKm;
    }

    public AssignmentStatus getAssignmentStatus() {
        return assignmentStatus;
    }

    public void setAssignmentStatus(AssignmentStatus assignmentStatus) {
        this.assignmentStatus = assignmentStatus;
    }

    public LocalDateTime getAssignedAt() {
        return assignedAt;
    }

    public void setAssignedAt(LocalDateTime assignedAt) {
        this.assignedAt = assignedAt;
    }

    public LocalDateTime getCompletedAt() {
        return completedAt;
    }

    public void setCompletedAt(LocalDateTime completedAt) {
        this.completedAt = completedAt;
    }

    public enum AssignmentStatus {
        ASSIGNED,
        ACCEPTED,
        RESPONDING,
        COMPLETED,
        DECLINED
    }
}