package com.campus.security.service;

import com.campus.security.model.IncidentReport;
import com.campus.security.model.Location;
import com.campus.security.model.SecurityOfficer;
import com.campus.security.model.User;
import com.campus.security.repository.IncidentReportRepository;
import com.campus.security.repository.LocationRepository;
import com.campus.security.repository.SecurityOfficerRepository;
import org.springframework.stereotype.Service;
import jakarta.annotation.PostConstruct;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class IncidentService {
    private final IncidentReportRepository incidentRepository;
    private final LocationRepository locationRepository;
    private final SecurityOfficerRepository officerRepository;
    private final NotificationService notificationService;

    public IncidentService(IncidentReportRepository incidentRepository,
                           LocationRepository locationRepository,
                           SecurityOfficerRepository officerRepository,
                           NotificationService notificationService) {
        this.incidentRepository = incidentRepository;
        this.locationRepository = locationRepository;
        this.officerRepository = officerRepository;
        this.notificationService = notificationService;
    }

    /**
     * Repairs legacy rows created before officer claiming was introduced.
     * A case cannot truthfully be UNDER_INVESTIGATION unless an officer has
     * claimed it, so only unassigned legacy rows are returned to REPORTED.
     */
    @PostConstruct
    public void normalizeLegacyUnassignedIncidents() {
        List<IncidentReport> legacy = incidentRepository
                .findByIncidentStatusAndAssignedOfficerIsNull(
                        IncidentReport.IncidentStatus.UNDER_INVESTIGATION);

        if (legacy.isEmpty()) return;

        LocalDateTime now = LocalDateTime.now();
        for (IncidentReport incident : legacy) {
            incident.setIncidentStatus(IncidentReport.IncidentStatus.REPORTED);
            incident.setLastUpdatedAt(now);
        }
        incidentRepository.saveAll(legacy);
        System.out.println("Normalized " + legacy.size()
                + " legacy unassigned incident(s) from UNDER_INVESTIGATION to REPORTED.");
    }

    public List<IncidentReport> getUnresolvedIncidents() {
        return incidentRepository.findByIncidentStatusNotInOrderByReportedAtDesc(
                List.of(IncidentReport.IncidentStatus.RESOLVED, IncidentReport.IncidentStatus.CLOSED));
    }

    public List<IncidentReport> getOfficerCases(User user) {
        SecurityOfficer officer = officerFor(user);
        return getUnresolvedIncidents().stream()
                .filter(i -> i.getAssignedOfficer() == null ||
                        i.getAssignedOfficer().getOfficerId().equals(officer.getOfficerId()))
                .filter(i -> i.getLocation() == null || i.getLocation().getCampus() == null ||
                        officer.getCampus() == null ||
                        i.getLocation().getCampus().getCampusId().equals(officer.getCampus().getCampusId()))
                .toList();
    }

    public IncidentReport createIncident(User user, Integer locationId, String incidentType,
                                         String description, IncidentReport.Severity severity) {
        if (incidentType == null || incidentType.isBlank()) throw new RuntimeException("Incident type is required.");
        if (description == null || description.isBlank()) throw new RuntimeException("Incident description is required.");
        if (locationId == null) throw new RuntimeException("Incident location is required.");
        if (severity == null) severity = IncidentReport.Severity.MEDIUM;
        Location location = locationRepository.findById(locationId)
                .orElseThrow(() -> new RuntimeException("Location not found."));
        IncidentReport incident = new IncidentReport();
        String type = incidentType.trim();
        incident.setTitle(type);
        incident.setUser(user);
        incident.setLocation(location);
        incident.setIncidentType(type);
        incident.setDescription(description.trim());
        incident.setSeverity(severity);
        incident.setIncidentStatus(IncidentReport.IncidentStatus.REPORTED);
        incident.setReportedAt(LocalDateTime.now());
        return incidentRepository.save(incident);
    }

    public List<IncidentReport> getUserIncidents(User user) { return incidentRepository.findByUser(user); }
    public List<IncidentReport> getAllIncidents() { return incidentRepository.findAllByOrderByReportedAtDesc(); }
    public List<IncidentReport> getIncidentsByStatus(IncidentReport.IncidentStatus status) { return incidentRepository.findByIncidentStatus(status); }

    public IncidentReport updateStatus(Integer incidentId, IncidentReport.IncidentStatus status, User currentUser) {
        if (status == null) throw new RuntimeException("Incident status is required.");
        if (status == IncidentReport.IncidentStatus.RESOLVED)
            throw new RuntimeException("Use Resolve Case and complete the officer review before resolving an incident.");

        IncidentReport incident = getIncident(incidentId);
        SecurityOfficer officer = officerFor(currentUser);

        if (status == IncidentReport.IncidentStatus.UNDER_INVESTIGATION) {
            if (incident.getAssignedOfficer() != null &&
                    !incident.getAssignedOfficer().getOfficerId().equals(officer.getOfficerId())) {
                throw new RuntimeException("This case is already assigned to another security officer.");
            }
            if (incident.getAssignedOfficer() == null) {
                incident.setAssignedOfficer(officer);
                incident.setAssignedAt(LocalDateTime.now());
            }
        } else if (incident.getAssignedOfficer() != null &&
                !incident.getAssignedOfficer().getOfficerId().equals(officer.getOfficerId())) {
            throw new RuntimeException("Only the assigned security officer can update this case.");
        }

        incident.setIncidentStatus(status);
        incident.setLastUpdatedAt(LocalDateTime.now());
        IncidentReport saved = incidentRepository.save(incident);
        notifyReporter(saved, "INCIDENT_STATUS_CHANGED",
                "Your " + saved.getIncidentType() + " report is now " + friendly(status) + ".");
        return saved;
    }

    public IncidentReport resolveIncident(Integer incidentId, User currentUser,
                                           IncidentReport.ResolutionValidity validity,
                                           String review) {
        if (validity == null) throw new RuntimeException("Select whether the report was genuine or false.");
        if (review == null || review.trim().length() < 10)
            throw new RuntimeException("Write an officer review of at least 10 characters before resolving the case.");

        IncidentReport incident = getIncident(incidentId);
        SecurityOfficer officer = officerFor(currentUser);
        if (incident.getAssignedOfficer() == null)
            throw new RuntimeException("Take the case by marking it UNDER INVESTIGATION before resolving it.");
        if (!incident.getAssignedOfficer().getOfficerId().equals(officer.getOfficerId()))
            throw new RuntimeException("Only the assigned security officer can resolve this case.");

        incident.setResolutionValidity(validity);
        incident.setOfficerReview(review.trim());
        incident.setIncidentStatus(IncidentReport.IncidentStatus.RESOLVED);
        incident.setResolvedAt(LocalDateTime.now());
        incident.setLastUpdatedAt(LocalDateTime.now());
        IncidentReport saved = incidentRepository.save(incident);
        notifyReporter(saved, "INCIDENT_RESOLVED",
                "Your " + saved.getIncidentType() + " report has been resolved by Campus Security.");
        return saved;
    }

    private SecurityOfficer officerFor(User user) {
        return officerRepository.findByEmployeeNumber(user.getStudentStaffNumber())
                .orElseThrow(() -> new RuntimeException("No security officer profile is linked to this account."));
    }

    private void notifyReporter(IncidentReport incident, String type, String message) {
        if (incident.getUser() != null) notificationService.notifyUser(incident.getUser(), type, message);
    }

    private String friendly(IncidentReport.IncidentStatus status) {
        return status.name().replace('_', ' ').toLowerCase();
    }

    private IncidentReport getIncident(Integer id) {
        return incidentRepository.findById(id).orElseThrow(() -> new RuntimeException("Incident report not found."));
    }
}
