package com.campus.security.repository;

import com.campus.security.model.AlertAssignment;
import com.campus.security.model.EmergencyAlert;
import com.campus.security.model.SecurityOfficer;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Collection;
import java.util.List;
import java.util.Optional;

public interface AlertAssignmentRepository
        extends JpaRepository<AlertAssignment, Integer> {

    List<AlertAssignment> findByOfficer(
            SecurityOfficer officer
    );

    List<AlertAssignment> findByOfficerOrderByAssignedAtDesc(
            SecurityOfficer officer
    );

    Optional<AlertAssignment> findByAssignmentIdAndOfficer(
            Integer assignmentId,
            SecurityOfficer officer
    );

    Optional<AlertAssignment> findByEmergencyAlertAndOfficer(
            EmergencyAlert emergencyAlert,
            SecurityOfficer officer
    );

    List<AlertAssignment>
    findByOfficerAndAssignmentStatusInOrderByAssignedAtDesc(
            SecurityOfficer officer,
            Collection<AlertAssignment.AssignmentStatus> statuses
    );
}