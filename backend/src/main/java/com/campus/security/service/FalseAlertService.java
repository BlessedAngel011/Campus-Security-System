package com.campus.security.service;

import com.campus.security.model.Administrator;
import com.campus.security.model.EmergencyAlert;
import com.campus.security.model.FalseAlert;
import com.campus.security.model.Notification;
import com.campus.security.model.User;
import com.campus.security.repository.FalseAlertRepository;
import com.campus.security.repository.EmergencyAlertRepository;
import com.campus.security.repository.NotificationRepository;
import com.campus.security.repository.UserRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class FalseAlertService {

    private final FalseAlertRepository falseAlertRepository;
    private final UserRepository userRepository;
    private final NotificationRepository notificationRepository;
    private final EmergencyAlertRepository emergencyAlertRepository;

    public FalseAlertService(
            FalseAlertRepository falseAlertRepository,
            UserRepository userRepository,
            NotificationRepository notificationRepository,
            EmergencyAlertRepository emergencyAlertRepository) {

        this.falseAlertRepository = falseAlertRepository;
        this.userRepository = userRepository;
        this.notificationRepository = notificationRepository;
        this.emergencyAlertRepository = emergencyAlertRepository;
    }

    public FalseAlert confirmFalseAlert(
            EmergencyAlert emergency,
            Administrator admin,
            String reason) {

        if (emergency.getUser() == null) {
            throw new RuntimeException(
                    "Emergency alert has no reporting user.");
        }

        User user = emergency.getUser();

        if (falseAlertRepository
                .existsByEmergencyAlertAndFalseAlertStatus(
                        emergency,
                        FalseAlert.FalseAlertStatus.CONFIRMED_FALSE)) {

            throw new RuntimeException(
                    "This emergency alert has already been confirmed as false.");
        }

        FalseAlert falseAlert = new FalseAlert();
        falseAlert.setEmergencyAlert(emergency);
        falseAlert.setUser(user);
        falseAlert.setReason(reason);
        falseAlert.setFalseAlertStatus(
                FalseAlert.FalseAlertStatus.CONFIRMED_FALSE);
        falseAlert.setCreatedAt(LocalDateTime.now());


        falseAlert = falseAlertRepository.save(falseAlert);

        int currentCount =
                user.getFalseAlertCount() == null
                        ? 0
                        : user.getFalseAlertCount();

        currentCount++;
        user.setFalseAlertCount(currentCount);

        if (currentCount >= 3) {
            user.setEmergencyButtonEnabled(false);
            sendDisabledNotification(user);
        }

        userRepository.save(user);

        emergency.setAlertStatus(
                EmergencyAlert.AlertStatus.FALSE_ALERT);

        emergencyAlertRepository.save(emergency);

        return falseAlert;
    }

    private void sendDisabledNotification(User user) {

        Notification notification = new Notification();
        notification.setUser(user);
        notification.setNotificationType(
                "EMERGENCY_BUTTON_DISABLED");
        notification.setMessage(
                "Your emergency button has been disabled because "
                        + "you submitted false alerts 3 times.");
        notification.setRead(false);
        notification.setCreatedAt(LocalDateTime.now());

        notificationRepository.save(notification);
    }

    public FalseAlert markNotFalse(
            EmergencyAlert emergency,
            Administrator admin) {

        if (emergency.getUser() == null) {
            throw new RuntimeException(
                    "Emergency alert has no reporting user.");
        }

        FalseAlert record = new FalseAlert();
        record.setEmergencyAlert(emergency);
        record.setUser(emergency.getUser());
        record.setFalseAlertStatus(
                FalseAlert.FalseAlertStatus.NOT_FALSE);
        record.setCreatedAt(LocalDateTime.now());

        return falseAlertRepository.save(record);
    }
}
