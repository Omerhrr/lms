<script setup lang="ts">
useSeoMeta({ title: 'Terms & Conditions - Infohive Technology Ltd.' })
const { config } = usePlatform()
const { content: site } = useSiteContent()
</script>

<template>
  <LegalPage title="Terms & Conditions" updated="October 2026" :html="site?.legal.terms_html" :custom-updated="site?.legal.updated">
    <p>These terms govern your use of the Infohive Technology Ltd. website and Learning Management System. By creating an account or using our services you agree to them.</p>
    <h2>Accounts</h2>
    <p>Keep your login details confidential and provide accurate information. You are responsible for activity on your account. We may suspend accounts that misuse the platform.</p>
    <h2>Courses and content</h2>
    <p>Course materials, videos and live classes are for your personal learning only. You may not copy, record, redistribute or resell them without permission. Instructor-provided content remains the property of its owners.</p>
    <h2>Payments and refunds</h2>
    <p>Paid courses are charged in the currency shown at checkout and processed securely by Paystack. Access is granted once payment is confirmed. Refund requests are handled according to our refund policy: [describe your refund policy].</p>
    <h2>Certificates</h2>
    <p>Certificates are issued on completing eligible courses and can be verified online by their serial number. We may revoke certificates obtained through misconduct.</p>
    <h2>Acceptable use</h2>
    <p>Do not attempt to disrupt the platform, access other users' data, share answers to assessments, or upload unlawful or harmful content. Be respectful in discussions and live classes.</p>
    <h2>Liability</h2>
    <p>We work to keep the platform available and accurate but provide it "as is". To the extent permitted by law, Infohive is not liable for indirect losses arising from its use.</p>
    <h2>Changes and contact</h2>
    <p>We may update these terms and will post the new version here. Contact us at <b>{{ config.contact?.email || '[Your Email Address]' }}</b> with any questions. These terms are governed by the laws of the Federal Republic of Nigeria.</p>
  </LegalPage>
</template>
