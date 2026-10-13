<script setup lang="ts">
useSeoMeta({ title: 'Privacy Policy - Infohive Technology Ltd.' })
const { config } = usePlatform()
const { content: site } = useSiteContent()
</script>

<template>
  <LegalPage title="Privacy Policy" updated="October 2026" :html="site?.legal.privacy_html" :custom-updated="site?.legal.updated">
    <p>Infohive Technology Ltd. ("Infohive", "we") respects your privacy. This policy explains what personal data we collect through our website and Learning Management System (LMS), why we collect it, and your choices.</p>
    <h2>Information we collect</h2>
    <ul>
      <li><b>Account details</b> - your name, email address and password (stored only as a secure hash).</li>
      <li><b>Learning records</b> - enrolments, lesson progress, quiz attempts, assignment submissions, live-class attendance, notes and certificates.</li>
      <li><b>Payments</b> - when you buy a course, payments are processed by Paystack. We receive the payment reference, amount and status; we never see or store your card details.</li>
      <li><b>Enquiries</b> - details you send through our contact form.</li>
      <li><b>Technical data</b> - basic logs (such as IP address) used for security and to prevent abuse.</li>
    </ul>
    <h2>How we use it</h2>
    <p>To provide and improve our services and courses, issue certificates, process payments, respond to enquiries, send service emails (such as password resets, receipts and class reminders) and keep the platform secure. We do not sell your personal data.</p>
    <h2>Sharing</h2>
    <p>We share data only with service providers that help us run the platform (for example hosting, database, email delivery, payment processing and video conferencing), and where required by law. Instructors can see the progress and submissions of learners in their courses.</p>
    <h2>Cookies</h2>
    <p>We use essential cookies to keep you signed in securely. These cookies cannot be read by scripts on the page and are not used for advertising.</p>
    <h2>Your rights</h2>
    <p>You can access and update your profile at any time, and you may ask us to correct or delete your personal data, subject to records we must keep by law (such as payment records). This policy is intended to align with the Nigeria Data Protection Act 2023.</p>
    <h2>Contact</h2>
    <p>Questions about privacy? Contact us at <b>{{ config.contact?.email || '[Your Email Address]' }}</b> or via our <NuxtLink to="/contact">contact page</NuxtLink>.</p>
  </LegalPage>
</template>
