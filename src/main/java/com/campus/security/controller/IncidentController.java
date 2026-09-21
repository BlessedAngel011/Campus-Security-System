package com.campus.security.controller;

import com.campus.security.model.IncidentEvidence;
import com.campus.security.model.IncidentReport;
import com.campus.security.model.User;
import com.campus.security.service.IncidentService;
import com.campus.security.service.UserService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/incidents")
public class IncidentController {

    private final IncidentService incidentService;
    private final UserService userService;

    public IncidentController(
            IncidentService incidentService,
            UserService userService) {

        this.incidentService = incidentService;
        this.userService = userService;
    }

    // Report an incident
    @PostMapping
    public ResponseEntity<?> createIncident(
            @RequestHeader("Authorization")
            String sessionToken,
            @RequestParam Integer locationId,
            @RequestParam String incidentType,
            @RequestParam String description,
            @RequestParam
            IncidentReport.Severity severity) {

        try {

            sessionToken =
                    sessionToken.replace("Bearer ", "");

            // Identify logged-in user automatically
            User user =
                    userService.getUserFromSession(
                            sessionToken);

            IncidentReport incident =
                    incidentService.createIncident(
                            user,
                            locationId,
                            incidentType,
                            description,
                            severity
                    );

            return ResponseEntity.ok(incident);

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // Get reports submitted by logged-in user
    @GetMapping("/my-reports")
    public ResponseEntity<?> getMyReports(
            @RequestHeader("Authorization")
            String sessionToken) {

        try {

            sessionToken =
                    sessionToken.replace("Bearer ", "");

            User user =
                    userService.getUserFromSession(
                            sessionToken);

            return ResponseEntity.ok(
                    incidentService.getUserIncidents(
                            user));

        } catch (RuntimeException e) {

            return ResponseEntity.status(401)
                    .body(e.getMessage());
        }
    }

    // Get reports by status
    @GetMapping("/status/{status}")
    public ResponseEntity<?> getByStatus(
            @PathVariable
            IncidentReport.IncidentStatus status) {

        return ResponseEntity.ok(
                incidentService.getIncidentsByStatus(
                        status));
    }

    // Change incident status
    @PutMapping("/{incidentId}/status")
    public ResponseEntity<?> updateStatus(
            @PathVariable Integer incidentId,
            @RequestParam
            IncidentReport.IncidentStatus status) {

        try {

            return ResponseEntity.ok(
                    incidentService.updateStatus(
                            incidentId,
                            status));

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // Upload incident evidence
    @PostMapping("/{incidentId}/evidence")
    public ResponseEntity<?> addEvidence(
            @RequestHeader("Authorization")
            String sessionToken,
            @PathVariable Integer incidentId,
            @RequestParam String fileName,
            @RequestParam String filePath,
            @RequestParam String fileType) {

        try {

            sessionToken =
                    sessionToken.replace("Bearer ", "");

            User user =
                    userService.getUserFromSession(
                            sessionToken);

            IncidentEvidence evidence =
                    incidentService.addEvidence(
                            incidentId,
                            user,
                            fileName,
                            filePath,
                            fileType
                    );

            return ResponseEntity.ok(evidence);

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // View incident evidence
    @GetMapping("/{incidentId}/evidence")
    public ResponseEntity<?> getEvidence(
            @PathVariable Integer incidentId) {

        try {

            List<IncidentEvidence> evidence =
                    incidentService.getIncidentEvidence(
                            incidentId);

            return ResponseEntity.ok(evidence);

        } catch (RuntimeException e) {

            return ResponseEntity.notFound().build();
        }
    }

    // Resolve incident
    @PutMapping("/{incidentId}/resolve")
    public ResponseEntity<?> resolveIncident(
            @PathVariable Integer incidentId) {

        try {

            return ResponseEntity.ok(
                    incidentService.resolveIncident(
                            incidentId));

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }
}