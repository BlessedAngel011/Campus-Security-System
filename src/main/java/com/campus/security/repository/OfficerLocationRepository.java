package com.campus.security.repository;

import com.campus.security.model.OfficerLocation;
import com.campus.security.model.SecurityOfficer;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface OfficerLocationRepository
        extends JpaRepository<OfficerLocation, Integer> {

    Optional<OfficerLocation> findTopByOfficerOrderByCapturedAtDesc(
            SecurityOfficer officer);
}