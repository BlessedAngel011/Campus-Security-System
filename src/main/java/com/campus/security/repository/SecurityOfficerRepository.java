package com.campus.security.repository;

import com.campus.security.model.SecurityOfficer;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface SecurityOfficerRepository
        extends JpaRepository<SecurityOfficer, Integer> {

    Optional<SecurityOfficer> findByEmployeeNumber(String employeeNumber);

    List<SecurityOfficer> findByAvailabilityStatus(
            SecurityOfficer.AvailabilityStatus status
    );
}