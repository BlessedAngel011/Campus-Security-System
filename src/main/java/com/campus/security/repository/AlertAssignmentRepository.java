package com.campus.security.repository;

import com.campus.security.model.AlertAssignment;
import com.campus.security.model.SecurityOfficer;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface AlertAssignmentRepository
        extends JpaRepository<AlertAssignment, Integer> {

    List<AlertAssignment> findByOfficer(SecurityOfficer officer);
}