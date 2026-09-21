package com.campus.security.repository;

import com.campus.security.model.Administrator;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface AdministratorRepository
        extends JpaRepository<Administrator, Integer> {

    Optional<Administrator> findByUniversityEmail(String universityEmail);

    Optional<Administrator> findByEmployeeNumber(String employeeNumber);
}