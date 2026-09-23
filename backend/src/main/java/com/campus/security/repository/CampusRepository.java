package com.campus.security.repository;

import com.campus.security.model.Campus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface CampusRepository extends JpaRepository<Campus, Integer> {

    boolean existsByCampusNameIgnoreCase(String campusName);

    Optional<Campus> findByCampusNameIgnoreCase(String campusName);
}