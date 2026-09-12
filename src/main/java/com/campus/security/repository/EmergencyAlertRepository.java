package com.campus.security.repository;

import com.campus.security.model.EmergencyAlert;
import com.campus.security.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface EmergencyAlertRepository
        extends JpaRepository<EmergencyAlert, Integer> {

    List<EmergencyAlert> findByUser(User user);

    List<EmergencyAlert> findByAlertStatus(
            EmergencyAlert.AlertStatus status
    );
}