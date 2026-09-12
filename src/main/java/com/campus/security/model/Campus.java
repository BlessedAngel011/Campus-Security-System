package com.campus.security.model;

import jakarta.persistence.*;

@Entity
@Table(name = "campuses")
public class Campus {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "campus_id")
    private Integer campusId;

    @Column(name = "campus_name", nullable = false)
    private String campusName;

    @Column(name = "campus_location", nullable = false)
    private String campusLocation;

    @Column(name = "contact_number")
    private String contactNumber;

    // Empty constructor required by JPA
    public Campus() {
    }

    // Constructor
    public Campus(String campusName, String campusLocation, String contactNumber) {
        this.campusName = campusName;
        this.campusLocation = campusLocation;
        this.contactNumber = contactNumber;
    }

    // Getter for campusId
    public Integer getCampusId() {
        return campusId;
    }

    // Setter for campusId
    public void setCampusId(Integer campusId) {
        this.campusId = campusId;
    }

    // Getter for campusName
    public String getCampusName() {
        return campusName;
    }

    // Setter for campusName
    public void setCampusName(String campusName) {
        this.campusName = campusName;
    }

    // Getter for campusLocation
    public String getCampusLocation() {
        return campusLocation;
    }

    // Setter for campusLocation
    public void setCampusLocation(String campusLocation) {
        this.campusLocation = campusLocation;
    }

    // Getter for contactNumber
    public String getContactNumber() {
        return contactNumber;
    }

    // Setter for contactNumber
    public void setContactNumber(String contactNumber) {
        this.contactNumber = contactNumber;
    }
}