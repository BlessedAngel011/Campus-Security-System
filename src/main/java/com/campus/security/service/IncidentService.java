package com.campus.security.service;

import com.campus.security.model.IncidentEvidence;
import com.campus.security.model.IncidentReport;
import com.campus.security.model.Location;
import com.campus.security.model.User;
import com.campus.security.repository.IncidentEvidenceRepository;
import com.campus.security.repository.IncidentReportRepository;
import com.campus.security.repository.LocationRepository;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class IncidentService {

    private final IncidentReportRepository incidentRepository;
    private final IncidentEvidenceRepository evidenceRepository;
    private final LocationRepository locationRepository;

    public IncidentService(
            IncidentReportRepository incidentRepository,
            IncidentEvidenceRepository evidenceRepository,
            LocationRepository locationRepository) {

        this.incidentRepository = incidentRepository;
        this.evidenceRepository = evidenceRepository;
        this.locationRepository = locationRepository;
    }

    // Create a new incident report
    public IncidentReport createIncident(
            User user,
            Integer locationId,
            String incidentType,
            String description,
            IncidentReport.Severity severity) {

        Location location = locationRepository
                .findById(locationId)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Location not found."));

        IncidentReport incident =
                new IncidentReport();

        // Automatically identify the person reporting
        incident.setUser(user);

        incident.setLocation(location);
        incident.setIncidentType(incidentType);
        incident.setDescription(description);
        incident.setSeverity(severity);

        incident.setIncidentStatus(
                IncidentReport.IncidentStatus.REPORTED);

        incident.setReportedAt(
                LocalDateTime.now());

        return incidentRepository.save(incident);
    }

    // Get all incidents reported by a particular user
    public List<IncidentReport> getUserIncidents(User user) {

        return incidentRepository.findByUser(user);
    }

    // Get incidents by status
    public List<IncidentReport> getIncidentsByStatus(
            IncidentReport.IncidentStatus status) {

        return incidentRepository
                .findByIncidentStatus(status);
    }

    // Change incident status
    public IncidentReport updateStatus(
            Integer incidentId,
            IncidentReport.IncidentStatus status) {

        IncidentReport incident =
                incidentRepository.findById(incidentId)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Incident not found."));

        incident.setIncidentStatus(status);

        // If incident is resolved, record resolution time
        if (status ==
                IncidentReport.IncidentStatus.RESOLVED) {

            incident.setResolvedAt(
                    LocalDateTime.now());
        }

        return incidentRepository.save(incident);
    }

    // Upload evidence
    public IncidentEvidence addEvidence(
            Integer incidentId,
            User uploadedBy,
            String fileName,
            String filePath,
            String fileType) {

        IncidentReport incident =
                incidentRepository.findById(incidentId)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Incident not found."));

        IncidentEvidence evidence =
                new IncidentEvidence();

        evidence.setIncidentReport(incident);
        evidence.setUploadedBy(uploadedBy);
        evidence.setFileName(fileName);
        evidence.setFilePath(filePath);
        evidence.setFileType(fileType);
        evidence.setUploadedAt(
                LocalDateTime.now());

        return evidenceRepository.save(evidence);
    }

    // Get evidence belonging to an incident
    public List<IncidentEvidence> getIncidentEvidence(
            Integer incidentId) {

        IncidentReport incident =
                incidentRepository.findById(incidentId)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Incident not found."));

        return evidenceRepository
                .findByIncidentReport(incident);
    }

    // Resolve an incident only when evidence exists
    public IncidentReport resolveIncident(
            Integer incidentId) {

        IncidentReport incident =
                incidentRepository.findById(incidentId)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Incident not found."));

        List<IncidentEvidence> evidence =
                evidenceRepository
                        .findByIncidentReport(incident);

        // Resolution is not allowed without evidence
        if (evidence.isEmpty()) {

            throw new RuntimeException(
                    "Incident cannot be resolved without evidence.");
        }

        incident.setIncidentStatus(
                IncidentReport.IncidentStatus.RESOLVED);

        incident.setResolvedAt(
                LocalDateTime.now());

        return incidentRepository.save(incident);
    }
}