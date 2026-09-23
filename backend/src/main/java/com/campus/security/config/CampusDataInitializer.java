package com.campus.security.config;

import com.campus.security.model.Campus;
import com.campus.security.repository.CampusRepository;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

/**
 * Adds the UFH campuses when the backend starts.
 * Existing campuses will not be duplicated.
 */
@Component
public class CampusDataInitializer implements ApplicationRunner {

    private final CampusRepository campusRepository;

    public CampusDataInitializer(CampusRepository campusRepository) {
        this.campusRepository = campusRepository;
    }

    @Override
    public void run(ApplicationArguments args) {
        addCampusIfMissing(
                "Alice Campus",
                "Alice, Eastern Cape",
                "040 602 2011"
        );

        addCampusIfMissing(
                "Bhisho Campus",
                "Bhisho, Eastern Cape",
                "043 783 5000"
        );

        addCampusIfMissing(
                "East London Campus",
                "East London, Eastern Cape",
                "043 704 7000"
        );
    }

    private void addCampusIfMissing(
            String campusName,
            String campusLocation,
            String contactNumber
    ) {
        boolean campusExists =
                campusRepository.existsByCampusNameIgnoreCase(campusName);

        if (!campusExists) {
            Campus campus = new Campus(
                    campusName,
                    campusLocation,
                    contactNumber
            );

            campusRepository.save(campus);
        }
    }
}