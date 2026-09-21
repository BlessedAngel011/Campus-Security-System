package com.campus.security.repository;

import com.campus.security.model.FalseAlert;
import com.campus.security.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface FalseAlertRepository
        extends JpaRepository<FalseAlert, Integer> {

    List<FalseAlert> findByUser(User user);

    long countByUserAndFalseAlertStatus(
            User user,
            FalseAlert.FalseAlertStatus status
    );
}