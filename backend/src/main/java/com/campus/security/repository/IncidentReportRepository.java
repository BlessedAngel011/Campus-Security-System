package com.campus.security.repository;

import com.campus.security.model.IncidentReport;
import com.campus.security.model.SecurityOfficer;
import com.campus.security.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface IncidentReportRepository
        extends JpaRepository<IncidentReport, Integer> {

    List<IncidentReport> findByUser(User user);

    List<IncidentReport> findByIncidentStatus(
            IncidentReport.IncidentStatus status
    );

    List<IncidentReport> findAllByOrderByReportedAtDesc();

    List<IncidentReport> findByAssignedOfficerOrderByReportedAtDesc(
            SecurityOfficer assignedOfficer
    );
}