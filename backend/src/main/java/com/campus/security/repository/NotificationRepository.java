package com.campus.security.repository;

import com.campus.security.model.Notification;
import com.campus.security.model.User;
import com.campus.security.model.SecurityOfficer;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface NotificationRepository
        extends JpaRepository<Notification, Integer> {

    List<Notification> findByUserOrderByCreatedAtDesc(User user);

    List<Notification> findByUserAndReadFalseOrderByCreatedAtDesc(User user);

    List<Notification> findByOfficerOrderByCreatedAtDesc(
            SecurityOfficer officer);

    List<Notification> findByOfficerAndReadFalseOrderByCreatedAtDesc(
            SecurityOfficer officer);

}
