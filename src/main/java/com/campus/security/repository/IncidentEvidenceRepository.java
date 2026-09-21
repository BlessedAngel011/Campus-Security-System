package com.campus.security.repository;

import com.campus.security.model.IncidentEvidence;
import com.campus.security.model.IncidentReport;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface IncidentEvidenceRepository
        extends JpaRepository<IncidentEvidence, Integer> {

    List<IncidentEvidence> findByIncidentReport(
            IncidentReport incidentReport);
}