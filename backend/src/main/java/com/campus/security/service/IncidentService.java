package com.campus.security.service;

import com.campus.security.model.IncidentEvidence;
import com.campus.security.model.IncidentReport;
import com.campus.security.model.Location;
import com.campus.security.model.User;
import com.campus.security.repository.IncidentEvidenceRepository;
import com.campus.security.repository.IncidentReportRepository;
import com.campus.security.repository.LocationRepository;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Service
public class IncidentService {

    private final IncidentReportRepository incidentRepository;
    private final IncidentEvidenceRepository evidenceRepository;
    private final LocationRepository locationRepository;

    // Evidence is stored outside the Java source tree.
    private final Path uploadDirectory =
            Paths.get("uploads", "incidents");

    public IncidentService(
            IncidentReportRepository incidentRepository,
            IncidentEvidenceRepository evidenceRepository,
            LocationRepository locationRepository) {

        this.incidentRepository = incidentRepository;
        this.evidenceRepository = evidenceRepository;
        this.locationRepository = locationRepository;
    }

    public IncidentReport createIncident(
            User user,
            Integer locationId,
            String incidentType,
            String description,
            IncidentReport.Severity severity) {

        if (incidentType == null || incidentType.isBlank()) {
            throw new RuntimeException("Incident type is required.");
        }

        if (description == null || description.isBlank()) {
            throw new RuntimeException("Incident description is required.");
        }

        if (severity == null) {
            severity = IncidentReport.Severity.MEDIUM;
        }

        Location location = locationRepository
                .findById(locationId)
                .orElseThrow(() ->
                        new RuntimeException("Location not found."));

        IncidentReport incident = new IncidentReport();

        // The reporting user comes from the authenticated session.
        incident.setUser(user);
        incident.setLocation(location);
        incident.setIncidentType(incidentType.trim());
        incident.setDescription(description.trim());
        incident.setSeverity(severity);
        incident.setIncidentStatus(
                IncidentReport.IncidentStatus.REPORTED);
        incident.setReportedAt(LocalDateTime.now());

        return incidentRepository.save(incident);
    }

    public List<IncidentReport> getUserIncidents(User user) {
        return incidentRepository.findByUser(user);
    }

    public List<IncidentReport> getAllIncidents() {
        return incidentRepository.findAllByOrderByReportedAtDesc();
    }

    public List<IncidentReport> getIncidentsByStatus(
            IncidentReport.IncidentStatus status) {

        return incidentRepository.findByIncidentStatus(status);
    }

    public IncidentReport updateStatus(
            Integer incidentId,
            IncidentReport.IncidentStatus status) {

        if (status == null) {
            throw new RuntimeException("Incident status is required.");
        }

        IncidentReport incident = getIncident(incidentId);

        // Resolution must go through /resolve so that the
        // mandatory image-evidence rule is always checked.
        if (status == IncidentReport.IncidentStatus.RESOLVED) {
            return resolveIncident(incidentId);
        }

        incident.setIncidentStatus(status);
        return incidentRepository.save(incident);
    }


    public IncidentEvidence addEvidence(
            Integer incidentId,
            User uploadedBy,
            MultipartFile file) {

        IncidentReport incident = getIncident(incidentId);

        if (file == null || file.isEmpty()) {
            throw new RuntimeException("Evidence file is required.");
        }

        String originalName = file.getOriginalFilename();

        if (originalName == null || originalName.isBlank()) {
            throw new RuntimeException("Evidence file name is invalid.");
        }

        // Prevent path traversal by using only the final file name.
        String safeOriginalName =
                Paths.get(originalName).getFileName().toString();

        String contentType = file.getContentType();

        if (contentType == null || contentType.isBlank()) {
            contentType = "application/octet-stream";
        }

        // Limit individual evidence files to 10 MB.
        if (file.getSize() > 10 * 1024 * 1024) {
            throw new RuntimeException(
                    "Evidence file must not be larger than 10 MB.");
        }

        try {
            Files.createDirectories(uploadDirectory);

            String storedName =
                    UUID.randomUUID() + "_" + safeOriginalName;

            Path destination =
                    uploadDirectory.resolve(storedName)
                            .normalize();

            if (!destination.startsWith(
                    uploadDirectory.toAbsolutePath().normalize())) {
                throw new RuntimeException("Invalid evidence file path.");
            }

            Files.copy(
                    file.getInputStream(),
                    destination,
                    StandardCopyOption.REPLACE_EXISTING);

            IncidentEvidence evidence =
                    new IncidentEvidence();

            evidence.setIncidentReport(incident);
            evidence.setFileName(safeOriginalName);
            evidence.setFilePath(destination.toString());
            evidence.setFileType(contentType);
            evidence.setUploadedAt(LocalDateTime.now());

            return evidenceRepository.save(evidence);

        } catch (IOException e) {
            throw new RuntimeException(
                    "Could not save evidence file.");
        }
    }

    public List<IncidentEvidence> getIncidentEvidence(
            Integer incidentId) {

        IncidentReport incident = getIncident(incidentId);

        return evidenceRepository
                .findByIncidentReport(incident);
    }

    /**
     * An incident can only be resolved when an IMAGE has been
     * uploaded as evidence.
     */
    public IncidentReport resolveIncident(
            Integer incidentId) {

        IncidentReport incident = getIncident(incidentId);

        List<IncidentEvidence> evidence =
                evidenceRepository.findByIncidentReport(incident);

        boolean hasImage = evidence.stream()
                .anyMatch(this::isImageEvidence);

        if (!hasImage) {
            throw new RuntimeException(
                    "Incident cannot be resolved without picture evidence.");
        }

        incident.setIncidentStatus(
                IncidentReport.IncidentStatus.RESOLVED);

        incident.setResolvedAt(LocalDateTime.now());

        return incidentRepository.save(incident);
    }

    private boolean isImageEvidence(IncidentEvidence evidence) {
        String fileType = evidence.getFileType();

        return fileType != null
                && fileType.toLowerCase()
                .startsWith("image/");
    }

    private IncidentReport getIncident(Integer incidentId) {
        return incidentRepository
                .findById(incidentId)
                .orElseThrow(() ->
                        new RuntimeException("Incident not found."));
    }
}
