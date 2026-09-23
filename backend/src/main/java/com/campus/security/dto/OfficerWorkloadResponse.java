package com.campus.security.dto;

import com.campus.security.model.SecurityOfficer;

import java.time.LocalDateTime;
import java.util.List;

public record OfficerWorkloadResponse(
        Integer officerId,
        String firstName,
        String lastName,
        String employeeNumber,
        String phoneNumber,
        String campusName,
        SecurityOfficer.AvailabilityStatus availabilityStatus,
        int activeCaseCount,
        List<WorkItem> activeCases
) {

    public record WorkItem(
            String caseType,
            Integer caseId,
            String title,
            String status,
            String location,
            String reporterName,
            String reporterNumber,
            LocalDateTime startedAt,
            LocalDateTime updatedAt
    ) {
    }
}