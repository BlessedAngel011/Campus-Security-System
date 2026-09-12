package com.campus.security.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "officer_locations")
public class OfficerLocation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "officer_location_id")
    private Integer officerLocationId;

    @ManyToOne
    @JoinColumn(name = "officer_id", nullable = false)
    private SecurityOfficer officer;

    @Column(name = "latitude", nullable = false)
    private Double latitude;

    @Column(name = "longitude", nullable = false)
    private Double longitude;

    @Column(name = "captured_at")
    private LocalDateTime capturedAt;

    public OfficerLocation() {
    }

    public Integer getOfficerLocationId() {
        return officerLocationId;
    }

    public void setOfficerLocationId(Integer officerLocationId) {
        this.officerLocationId = officerLocationId;
    }

    public SecurityOfficer getOfficer() {
        return officer;
    }

    public void setOfficer(SecurityOfficer officer) {
        this.officer = officer;
    }

    public Double getLatitude() {
        return latitude;
    }

    public void setLatitude(Double latitude) {
        this.latitude = latitude;
    }

    public Double getLongitude() {
        return longitude;
    }

    public void setLongitude(Double longitude) {
        this.longitude = longitude;
    }

    public LocalDateTime getCapturedAt() {
        return capturedAt;
    }

    public void setCapturedAt(LocalDateTime capturedAt) {
        this.capturedAt = capturedAt;
    }
}